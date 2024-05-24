import datetime
import time
import random
import logging

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import TimeoutException

logging.basicConfig(
    format='[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', 
    level=logging.INFO
)

class ExtratoTipo(object):
    Futuro = 'futuro'
    Ultimos7dias = 'últimos 7 dias'
    Ultimos15dias = 'últimos 15 dias'
    Ultimos30dias = 'últimos 30 dias'
    Ultimos60dias = 'últimos 60 dias'
    Ultimos90dias = 'últimos 90 dias'
    MesCompleto = 'mês completo (desde 2002)'

class CartaoFaturaTipo(object):
    Atual = 0
    Anterior = -1
    Proximas = 1

class MesAnoException(Exception):
    pass

class ScrawlerItau:

    _meses = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12
    }

    _meses_abr = {
        "jan": 1,
        "fev": 2,
        "mar": 3,
        "abr": 4,
        "mai": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8,
        "set": 9,
        "out": 10,
        "nov": 11,
        "dez": 12
    }

    cartao_fatura_ref = {}

    def __init__(self, agencia, conta, senha):
        self._agencia = agencia
        self._conta = conta
        self._senha = senha

    def _expand_home(self):

        logging.info('expandir cartões, se necessário')
        tries = 1
        while True:
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.element_to_be_clickable((By.ID,'cartao-card-accordion')))
                if s_elem.get_attribute('aria-expanded') == 'false':
                    s_elem.click()
                break
            except Exception as e:
                if tries == 3:
                    raise e
                try:
                    self.s_action.move_by_offset(0,0).click().perform()
                except Exception as e2:
                    pass
            tries += 1

        logging.info('expandir saldo e extrado da conta, se necessário')
        tries = 1
        while True:
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.element_to_be_clickable((By.ID,'saldo-extrato-card-accordion')))
                if s_elem.get_attribute('aria-expanded') == 'false':
                    s_elem.click()
                break
            except Exception as e:
                if tries == 3:
                    raise e
                try:
                    self.s_action.move_by_offset(0,0).click().perform()
                except Exception as e2:
                    pass
            tries += 1

    def open(self):

        # https://www.bacancytechnology.com/qanda/qa-automation/configuring-geckodriver-in-linux-to-use-with-selenium
        # https://www.omgubuntu.co.uk/2022/04/how-to-install-firefox-deb-apt-ubuntu-22-04#:%7E:text=Installing%20Firefox%20via%20Apt%20(Not%20Snap)&text=You%20add%20the%20Mozilla%20Team,%2C%20bookmarks%2C%20and%20other%20data.
        logging.info('abrir browser e acessar site')
        self.s_driver = webdriver.Firefox()
        self.s_driver.get('http://www.itau.com.br')
        self.s_wait = WebDriverWait(self.s_driver,10)
        self.s_action = ActionChains(self.s_driver)

        time.sleep(3)
        logging.info('inserir agência e conta')
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'idl-menu-agency')))
        s_elem.send_keys(self._agencia)
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'idl-menu-account')))
        s_elem.send_keys(self._conta)
        s_elem.send_keys(Keys.RETURN)

        time.sleep(4)
        logging.info('inserir senha')
        for digito in self._senha:
            tries = 1
            click = False
            while not click:
                try:
                    time.sleep(random.randint(0,2))
                    s_elem = self.s_wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT,digito)))
                    s_elem.click()
                    click = True
                except Exception as e:
                    if tries == 3:
                        raise e
                    tries += 1
        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT,'acessar')))
        s_elem.click()

        logging.info('aguardar carregamento inicial')
        time.sleep(6)

        logging.info('expandir home')
        self._expand_home()
        time.sleep(3)
        self.last_location = 'home'

    def go_home(self):
        if self.last_location == 'home':
            return
        
        logging.info('ir para página inicial')
        tries = 1
        while True:
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.element_to_be_clickable((By.ID,'HomeLogo')))
                s_elem.click()
                break
            except Exception as e:
                if tries == 3:
                    raise e
                try:
                    self.s_action.move_by_offset(0,0).click().perform()
                except Exception as e2:
                    pass
            tries += 1

        logging.info('expandir home')
        self._expand_home()
        time.sleep(3)
        self.last_location = 'home'

    def get_saldo(self):
        self.go_home()

        s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'saldo')))
        saldo = s_elem.text.strip()
        saldo = saldo.replace('R$ ','')
        saldo = saldo.replace('.','')
        saldo = saldo.replace(',','.')
        saldo = float(saldo)

        return saldo

    def get_extrato(self, tipo, mes=0, ano=0):
        if tipo == ExtratoTipo.MesCompleto:
            if not (mes >= 1 and mes <= 12):
                raise MesAnoException('Parâmetros mes e/ou ano inválido(s).')
            if not (ano >= 1970 and ano <= datetime.date.today().year):
                raise MesAnoException('Parâmetros mes e/ou ano inválido(s).')
        else:
            if mes != 0 or ano != 0:
                raise MesAnoException('Utilizar mes e ano somente para "tipo=ExtratoTipo.MesCompleto".')

        if self.last_location != 'extrato':
            self.go_home()

            # abrir extrato
            s_elem = self.s_wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'btn-bank-statement')))
            s_elem.click()
        
        self.last_location = 'extrato'

        # definir período
        tries = 1
        while True:
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.ID,'periodoFiltro')))
                s_elem.click()

                s_elem_list = self.s_wait.until(EC.visibility_of_element_located((By.ID,'periodoFiltroList')))
                for option in s_elem_list.find_elements(By.CLASS_NAME, 'form-element-group__select-option'):
                    if tipo == option.text.strip():
                        option.click()
                        break
                break
            except Exception as e:
                if tries == 3:
                    raise e
                tries += 1

        dupl = {}
        base = []

        # Lançamentos Futuros
        if tipo == ExtratoTipo.Futuro:

            # clicar em lançamentos futuros
            time.sleep(3)
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.ID,'btn-aba-lancamentos-futuros')))
            s_elem.click()

            # extrair lançamentos futuros
            try:
                time.sleep(3)
                s_elem = self.s_wait.until(EC.presence_of_element_located((By.ID,'corpo-tabela-lancamentos-futuros'))) \
                    .find_elements_by_class_name('table-extract__row')
                for s_elem_row in s_elem:
                    s_elem_cols = s_elem_row.find_elements_by_tag_name('div')
                    date = datetime.datetime.strptime(s_elem_cols[0].text.strip(),'%d/%m/%Y').strftime('%Y-%m-%d')
                    name = s_elem_cols[1].text.strip()
                    value = 0 - float(s_elem_cols[2].text.strip().replace('.','').replace(',','.'))
                    
                    dupl_key = f'{date}|{name}|{value}'
                    dupl[dupl_key] = dupl.get(dupl_key, 0) + 1
                    if dupl[dupl_key] > 1:
                        name = f'{name} ({str(dupl[dupl_key])})'

                    base.append({
                        "date": date,
                        "name": name,
                        "value": value
                    })
            except TimeoutException as ex:
                print(f'TimeoutException has been thrown: {str(ex)}')

        # Extrato
        else:
            # filtrar período para mês completo
            if tipo == ExtratoTipo.MesCompleto:

                time.sleep(3)

                filter_date = datetime.date(ano, mes, 1)

                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'month-picker__icon__placeholder')))
                self.s_driver.execute_script('arguments[0].click()', s_elem)

                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'month-picker__input')))
                s_elem.clear()
                s_elem.send_keys(filter_date.strftime('%m')+filter_date.strftime('%Y'))

                s_elem = self.s_wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'month-picker__button')))
                s_elem.click()

            # extrair lançamentos
            time.sleep(3)
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.ID,'extrato-grid-lancamentos')))
            for s_elem_row in s_elem.find_elements(By.CLASS_NAME, 'extrato-tabela-pf'):
                s_elem_cols = s_elem_row.find_elements(By.CLASS_NAME, 'extrato-impressao-zebrado')
                if len(s_elem_cols) >= 3 and s_elem_cols[2].text.strip() != '':
                    date = datetime.datetime.strptime(s_elem_cols[0].text.strip(),'%d/%m/%Y').strftime('%Y-%m-%d')
                    name = s_elem_cols[1].text.strip()
                    value = float(s_elem_cols[2].text.strip().replace('.','').replace(',','.'))

                    dupl_key = f'{date}|{name}|{value}'
                    dupl[dupl_key] = dupl.get(dupl_key, 0) + 1
                    if dupl[dupl_key] > 1:
                        name = f'{name} ({str(dupl[dupl_key])})'

                    base.append({
                        "date": date,
                        "name": name,
                        "value": value
                    })

        return base

    def list_cartoes(self):
        self.go_home()

        s_elem_rows = self.s_wait.until(EC.presence_of_element_located((By.ID,'content-cartao-card-accordion')))

        def divide_chunks(l, n): 
            for i in range(0, len(l), n):  
                yield l[i:i + n] 

        def process_content_cartao_card(content_cartao):
            splited = content_cartao.text.split('\n')
            splited_without_header = splited[1:]
            aux = []
            for splited in divide_chunks(splited_without_header, 3):
                splited[2] = splited[2].split(' ')
                aux.append({
                    "name": splited[0].strip(),
                    "due_date": datetime.datetime.strptime(splited[2][0],'%d/%m/%Y').strftime('%Y-%m-%d'),
                    "value": float(splited[2][1].replace('.', '').replace(',', '.')),
                    "status": splited[2][2]
                })
            return aux

        return process_content_cartao_card(s_elem_rows)

    def get_cartao_fatura(self, nome, tipo=CartaoFaturaTipo.Atual):
        base = []
        before = None

        if self.last_location != 'cartao_fatura_'+nome:
            self.go_home()
            self.s_wait.until(EC.element_to_be_clickable((By.LINK_TEXT,nome))).click()
        self.last_location = 'cartao_fatura_'+nome

        # ref
        fatref_date = self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'c-category-status__venc'))) \
            .text.strip().replace('venc. ','').split('/')
        fatref = datetime.date(2000+int(fatref_date[2]),int(fatref_date[1]),int(fatref_date[0]))
        if nome not in self.cartao_fatura_ref:
            self.cartao_fatura_ref[nome] = fatref
        else:
            while fatref != self.cartao_fatura_ref[nome]:
                if fatref < self.cartao_fatura_ref[nome]:
                    class_click = 'icon-itaufonts_seta_right'
                else:
                    class_click = 'icon-itaufonts_seta'
                self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,class_click))).click()
                fatref_date = self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'c-category-status__venc'))) \
                    .text.strip().replace('venc. ','').split('/')
                fatref = datetime.date(2000+int(fatref_date[2]),int(fatref_date[1]),int(fatref_date[0]))

        # acessar fatura anterior
        if tipo == CartaoFaturaTipo.Anterior:
            time.sleep(4)
            self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'icon-itaufonts_seta'))).click()

        # acessar próxima fatura
        elif tipo == CartaoFaturaTipo.Proximas:
            time.sleep(2)
            tries = 1
            clicked = False
            while not clicked:
                try:
                    time.sleep(2)
                    self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'icon-itaufonts_seta_right'))).click()
                    clicked = True
                except Exception as e:
                    if tries == 3:
                        raise e
                    tries += 1

        # loop
        while True:
            time.sleep(4)

            dupl = {}
            items = []
            
            # vencimento fatura
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'c-category-status__venc')))
            dates = s_elem.text.strip().replace('venc. ','').split('/')
            invoice_due_date = datetime.date(2000+int(dates[2]),int(dates[1]),int(dates[0]))
            invoice_due_year = invoice_due_date.year

            # parar loop se fatura anterior for igual que fatura atual
            if (tipo == CartaoFaturaTipo.Proximas and 
                before != None and before == invoice_due_date):
                break

            # valor fatura
            s_elem = self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'c-category-status__total')))
            invoice_value = float(s_elem.text.strip().replace('R$','').replace('.','').replace(',','.'))

            for s_elem_type in self.s_wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME,'lancamento'))).find_elements_by_xpath('./*'):

                try:
                    type_name = s_elem_type.find_element_by_tag_name('h3').text.strip()
                except:
                    break

                if type_name in ['lançamentos nacionais','lançamentos internacionais']:

                    for s_elem_card in s_elem_type.find_elements_by_class_name('fatura__tipo'):

                        card_name = s_elem_card.find_element_by_tag_name('h4').text.strip()

                        last_date = None
                        for s_elem_row in s_elem_card.find_elements_by_class_name('linha-valor-total'):

                            # columns
                            s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
                            # date
                            dates = s_elem_cols[0].text.strip().split(' / ')
                            if dates == ['']:
                                date = last_date
                            else:
                                month = self._meses_abr[dates[1]] if len(dates[1]) == 3 else self._meses[dates[1]]
                                date = datetime.date(invoice_due_year,month,int(dates[0])).isoformat()
                                last_date = date
                            # name
                            name = s_elem_cols[1].text.strip()
                            # value
                            values = s_elem_cols[2].text.strip().split('\n')
                            value = -1 * float(
                                values[0 if len(values) == 1 else 1].replace('R$ ','').replace('.','').replace(',','.'))
                            
                            dupl_key = date + '|' + name + '|' + str(value)
                            dupl[dupl_key] = dupl.get(dupl_key, 0) + 1
                            if dupl[dupl_key] > 1:
                                name = name + ' ('+str(dupl[dupl_key])+')'

                            # item
                            items.append({
                                "group": card_name + ' - ' + type_name,
                                "date": date,
                                "name": name,
                                "value": value
                            })

                elif type_name == 'compras parceladas':

                    for s_elem_card in s_elem_type.find_elements_by_class_name('fatura__tipo'):

                        card_name = s_elem_card.find_element_by_tag_name('h4').text.strip()
                        
                        try:
                            s_elem_tbody = s_elem_type.find_element_by_tag_name('tbody')
                        except Exception as e:
                            s_elem_tbody = None
                        
                        if s_elem_tbody:

                            last_date = None
                            for s_elem_row in s_elem_tbody.find_elements_by_tag_name('tr'):

                                # columns
                                s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
                                # date
                                dates = s_elem_cols[0].text.strip().split(' / ')
                                if dates == ['']:
                                    date = last_date
                                else:
                                    month = self._meses_abr[dates[1]] if len(dates[1]) == 3 else self._meses[dates[1]]
                                    date = datetime.date(invoice_due_year,month,int(dates[0])).isoformat()
                                    last_date = date
                                # name
                                name = s_elem_cols[1].text.strip()
                                # value
                                values = s_elem_cols[2].text.strip().split('\n')
                                value = -1 * float(
                                    values[0 if len(values) == 1 else 1].replace('R$ ','').replace('.','').replace(',','.'))
                                
                                dupl_key = date + '|' + name + '|' + str(value)
                                dupl[dupl_key] = dupl.get(dupl_key, 0) + 1
                                if dupl[dupl_key] > 1:
                                    name = name + ' ('+str(dupl[dupl_key])+')'

                                # item
                                items.append({
                                    "group": card_name + ' - ' + type_name,
                                    "date": date,
                                    "name": name,
                                    "value": value
                                })

                else:

                    try:
                        s_elem_tbody = s_elem_type.find_element_by_tag_name('tbody')
                    except Exception as e:
                        s_elem_tbody = None
                    
                    if s_elem_tbody:

                        last_date = None
                        for s_elem_row in s_elem_tbody.find_elements_by_tag_name('tr'):

                            # columns
                            s_elem_cols = s_elem_row.find_elements_by_tag_name('td')
                            # date
                            dates = s_elem_cols[0].text.strip().split(' / ')
                            if dates == ['']:
                                date = last_date
                            else:
                                month = self._meses_abr[dates[1]] if len(dates[1]) == 3 else self._meses[dates[1]]
                                date = datetime.date(invoice_due_year,month,int(dates[0])).isoformat()
                                last_date = date
                            # name
                            name = s_elem_cols[1].text.strip()
                            # value
                            values = s_elem_cols[2].text.strip().split('\n')
                            value = -1 * float(
                                values[0 if len(values) == 1 else 1].replace('R$ ','').replace('.','').replace(',','.'))
                            
                            dupl_key = date + '|' + name + '|' + str(value)
                            dupl[dupl_key] = dupl.get(dupl_key, 0) + 1
                            if dupl[dupl_key] > 1:
                                name = name + ' ('+str(dupl[dupl_key])+')'

                            # item
                            items.append({
                                "group": type_name,
                                "date": date,
                                "name": name,
                                "value": value
                            })

            base.append({
                "name": nome,
                "due_date": invoice_due_date.strftime('%Y-%m-%d'),
                "amount_value": invoice_value,
                "items": items
            })

            if tipo == CartaoFaturaTipo.Proximas:
                before = invoice_due_date
                self.s_wait.until(EC.presence_of_element_located((By.CLASS_NAME,'icon-itaufonts_seta_right'))).click()
            else:
                break

        return base

    def close(self):
        self.s_driver.quit()
