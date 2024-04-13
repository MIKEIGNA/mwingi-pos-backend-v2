
import json
from pprint import pprint
import requests
import logging

from django.conf import settings
from core.db_utils import DbUtils

from traqsale_cloud.celery import app as celery_app

from core.logger_manager import LoggerManager

# Connector request types
MWINGI_CONN_RECEIPT_REQUEST=0 
MWINGI_CONN_PRODUCT_REQUEST=1 
MWINGI_CONN_TAX_REQUEST=2
MWINGI_CONN_EMPLOYEE_REQUEST=3 
MWINGI_CONN_INVENTORY_REQUEST=4
MWINGI_CONN_CUSTOMER_REQUEST=5

# pylint: disable=bare-except
# pylint: disable=broad-except 

# Sends data to the Mwingi connector in the background
@celery_app.task(name="send_data_to_connector_task")
def send_data_to_connector_task(request_type, model_reg_no, payload=None):
    """
    Sends data to the Mwingi connector in the background
    """

    # If we are in testing mode, we don't want to send data to the connector
    if not settings.TESTING_MODE and not DbUtils.check_if_we_are_in_production(): 
        return

    try:
        _SendDataToConnector(request_type, model_reg_no, payload=payload)
    except Exception:
        LoggerManager.log_critical_error()



class _SendDataToConnector:
    def __init__(self, request_type, model_reg_no, payload) -> None:
        self.request_type = request_type
        self.model_reg_no = model_reg_no
        self.payload = payload

        self.request_timeout = 30

        if request_type == MWINGI_CONN_RECEIPT_REQUEST:
            self._send_receipt_data()
        elif request_type == MWINGI_CONN_PRODUCT_REQUEST:
            self._send_product_data()
        elif request_type == MWINGI_CONN_TAX_REQUEST:
            self._send_tax_data()
        elif request_type == MWINGI_CONN_EMPLOYEE_REQUEST:
            self._send_employee_data()
        elif request_type == MWINGI_CONN_CUSTOMER_REQUEST:
            self._send_customer_data()
        elif request_type == MWINGI_CONN_INVENTORY_REQUEST:
            self._send_inventory_data()
        
    def _send_receipt_data(self):
        """
        Sends receipt data to mwingi connector
        """
        connector_url = settings.MWINGI_CONN_RECEIPTS_URL
        own_url = f'{settings.MY_SITE_URL}/api/webhook/receipts/?reg_no={self.model_reg_no}'
        data_identifier = 'connector_receipt' 

        self._send_data_to_connector(connector_url, own_url, data_identifier)

    def _send_product_data(self):
        """
        Sends product data to mwingi connector
        """

        connector_url = settings.MWINGI_CONN_PRODUCTS_URL
        own_url = f'{settings.MY_SITE_URL}/api/webhook/products/?reg_no={self.model_reg_no}'
        data_identifier = 'connector_product'

        self._send_data_to_connector(connector_url, own_url, data_identifier)

    def _send_tax_data(self):
        """
        Sends tax data to mwingi connector
        """

        connector_url = settings.MWINGI_CONN_TAXES_URL
        own_url = f'{settings.MY_SITE_URL}/api/webhook/taxes/?reg_no={self.model_reg_no}'
        data_identifier = 'connector_tax'

        self._send_data_to_connector(connector_url, own_url, data_identifier)

    def _send_employee_data(self):
        """
        Sends employee data to mwingi connector
        """

        connector_url = settings.MWINGI_CONN_EMPLOYEES_URL
        own_url = f'{settings.MY_SITE_URL}/api/webhook/employees/?reg_no={self.model_reg_no}'
        data_identifier = 'connector_employee'

        self._send_data_to_connector(connector_url, own_url, data_identifier)

    def _send_inventory_data(self):
        """
        Sends inventory data to mwingi connector
        """

        connetctor_urls = [
            settings.MWINGI_CONN_INVENTORY_URL,
            settings.MWINGI_OLD_CONN_INVENTORY_URL
        ]

        for connector_url in connetctor_urls:

            if settings.TESTING_MODE:
                payload = {
                    'payload': {
                        'model': 'connector_inventory', 
                        'payload': str(self.payload)
                    }
                }

                logger = logging.getLogger('test_firebase_sender_logger')
                logger.info(json.dumps(payload))

            else:
                # Send data to connector rather than firebase

                try:

                    response = requests.post(
                        connector_url, 
                        json=self.payload, 
                        timeout=self.request_timeout
                    )

                    if response.status_code != 200:
                        LoggerManager.log_critical_error(
                            additional_message=f'Connector Error {json.dumps(self.payload)}'
                        )

                except Exception:
                    LoggerManager.log_critical_error()

    def _send_customer_data(self):
        """
        Sends customer data to mwingi connector
        """

        connector_url = settings.MWINGI_CONN_CUSTOMER_URL
        own_url = f'{settings.MY_SITE_URL}/api/webhook/customers/?reg_no={self.model_reg_no}'
        data_identifier = 'connector_customer'

        self._send_data_to_connector(connector_url, own_url, data_identifier)

    def _send_data_to_connector(self, connector_url, own_url, data_identifier):
        """
        Sends data to connector
        """

        payload = {}
        status_code = 200
        if settings.TESTING_MODE:
            payload = {
                'payload': {
                    'model': data_identifier, 
                    'payload': f'{self.model_reg_no} payload data'
                }
            }
            status_code = 200

        else:
            response = requests.get(url=own_url, timeout=30)

            if response.status_code == 200:
                payload = response.json()
                status_code = 200
            else:
                status_code = response.status_code

            
        if status_code and payload:

            if settings.TESTING_MODE:
                logger = logging.getLogger('test_firebase_sender_logger')
                logger.info(json.dumps(payload))

            else:

                # Send data to connector rather than firebase
                response = requests.post(
                    connector_url, 
                    json=payload, 
                    timeout=self.request_timeout
                )
                
                if response.status_code != 200:
                    LoggerManager.log_critical_error(
                        additional_message=f'Connector Error {json.dumps(payload)}'
                    )