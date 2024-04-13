from django.conf import settings

def c2b_return_data():
    data = {
            "TransactionType":"",
            "TransID":"LGR219G3EY",
            "TransTime":"20190425125829",
            "TransAmount":"100.00",
            "BusinessShortCode":settings.MPESA_BUSINESS_SHORTCODE,
            "BillRefNumber":"41188490695",
            "InvoiceNumber":"",
            "OrgAccountBalance":"",
            "ThirdPartyTransID":"",
            "MSISDN":"254708374140",
            "FirstName":"John",
            "MiddleName":"J",
            "LastName":"Doe"
            }
    
    return data