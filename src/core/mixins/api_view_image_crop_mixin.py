from rest_framework.response import Response
from rest_framework import status

# TODO Remove this
class ApiCropImageMixin:
    
    def update(self, request, *args, **kwargs):
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
    
        serializer.is_valid(raise_exception=True)
                
        # ********** Do your stuff here

        #  Skip this op if new image has not been passed
        if serializer.validated_data.get('image', None):

            try:
    
                image = serializer.validated_data['image']
                
                if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    
                    error_data = {
                        'error': "Allowed image extensions are .jpg, .jpeg and .png"
                    }
                    return Response(
                        error_data, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            except: # pylint: disable=bare-except
                error_data = {'error': "You did not provide a valid image"}
                
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        else:
            print("**** Skipping image1 ")
        
        # ********** Do your stuff here
        
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
            
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        serializer.save()


