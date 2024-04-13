from django.utils import timezone

from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status

from stores.models import Store

from api.serializers import FirebaseDeviceSerializer

from firebase.models import FirebaseDevice

class FirebaseDeviceView(generics.GenericAPIView):
    serializer_class = FirebaseDeviceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        store = None

        try:
            store = Store.objects.get(
                reg_no=serializer.validated_data['store_reg_no']
            )
        except: # pylint: disable=bare-except
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)


        # Update firebase device or create a new one if it does not exist
        try:
            device = FirebaseDevice.objects.get(token=token)
            device.user = request.user
            device.store = store
            device.is_current_active = True
            device.save()

        except: # pylint: disable=bare-except
            FirebaseDevice.objects.create(
                token=token,
                user=request.user,
                store=store,
                is_current_active = True,
                last_login_date =timezone.now()
            )

        return Response({"detail": "New key has been saved."})
        