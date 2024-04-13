from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
                                  
from sales.models import Receipt


class ReceiptEmailHelpers:

    @staticmethod
    def populate_context_dict(context, receipt, request_user):

        local_date = f'Date: {receipt.get_created_date(request_user.get_user_timezone())}'
        local_date = 'Date: {}'.format(
            receipt.get_created_date(request_user.get_user_timezone())
        )

        context['header_footer'] = receipt.store.get_receipt_setting()
        context['local_date'] = local_date
        context['receipt'] = receipt
        context['receipt_data'] = receipt.get_receipt_view_data()

        return context

class ReceiptEmailIndexView(LoginRequiredMixin, ListView):
    template_name = 'sales/index.html'
    context_object_name = 'latest_receipt_list'
    paginate_by = 10
    model = Receipt
    
    def get_queryset(self):       
        queryset = super(ReceiptEmailIndexView, self).get_queryset()
        queryset = queryset.order_by('-created_date')
        
        return queryset

class ReceiptEmailView(LoginRequiredMixin, DetailView):
    model = Receipt
    context_object_name = 'receipt'
    template_name = 'sales/receipt_email_template.html'

    def get_context_data(self, **kwargs):
        context = super(ReceiptEmailView, self).get_context_data(**kwargs)

        receipt = self.get_object()

        context = ReceiptEmailHelpers.populate_context_dict(
            context=context,
            receipt=receipt,
            request_user=self.request.user
        )

        return context

 