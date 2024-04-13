from rest_framework import serializers


class MpesaSerializer(serializers.Serializer):
    TransactionType =   serializers.CharField(required=True, allow_blank=True, max_length=100)
    TransID =           serializers.CharField(required=True, max_length=100)
    TransTime =         serializers.IntegerField(required=True)
    TransAmount =       serializers.DecimalField(required=True, max_digits=30, decimal_places=2)
    BusinessShortCode = serializers.IntegerField(required=True)
    BillRefNumber =     serializers.IntegerField(required=True)
    InvoiceNumber =     serializers.CharField(required=True, allow_blank=True, max_length=100)
    OrgAccountBalance = serializers.CharField(required=True, allow_blank=True, max_length=100)
    ThirdPartyTransID = serializers.CharField(required=True, allow_blank=True, max_length=100)
    MSISDN =            serializers.IntegerField(required=True)
    FirstName =         serializers.CharField(required=True, allow_blank=True, max_length=100)
    MiddleName =        serializers.CharField(required=True, allow_blank=True, max_length=100)
    LastName =          serializers.CharField(required=True, allow_blank=True, max_length=100)
    
    
    """
    Make sure all interger fields have validations to prevent Sql overflow errors
    
    * BusinessShortCode ==> Has is tested in MpesaPaymentView before going in the DB
    * BillRefNumber ==> Has is tested in AcceptPayment() before going in the DB
    """
    def validate_TransTime(self, TransTime):
        
        """Raise a serializers.ValidationError if the BusinessShortCode is bigger than normal
        """
        
        if len(str(TransTime)) > 16:
            raise serializers.ValidationError("Wrong TransTime format Was Provided")
            
        return TransTime
    

    

    

    
    
