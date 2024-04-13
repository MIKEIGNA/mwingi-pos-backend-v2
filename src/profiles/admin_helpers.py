from django.contrib import messages
from django.utils.translation import ngettext
from django.http import HttpResponseRedirect
from django.shortcuts import render

from billing.utils.payment_utils.price_gen import PriceGeneratorClass
from billing.utils.payment_utils.accept_payment import AcceptPayment

from .models import EmployeeProfile

class ProfileAdminPaymentActionMixin:

    def make_payment_for_1_month(self, request, queryset):
        """
        Creates a 1 month plan admin action
        """

        action_name = "make_payment_for_1_month"
        num_of_months = 1

        return self.render_intermediate_template(
            request, queryset, action_name, num_of_months)
    
    make_payment_for_1_month.short_description = "1 Month Plan For Top Profile"

    def make_payment_for_6_months(self, request, queryset):
        """
        Creates a 6 months plan admin action
        """

        action_name = "make_payment_for_6_months"
        num_of_months = 6

        return self.render_intermediate_template(
            request, queryset, action_name, num_of_months)
    
    make_payment_for_6_months.short_description = "6 Months Plan For Top Profile"

    def make_payment_for_1_year(self, request, queryset):
        """
        Creates a 1 year plan admin action
        """

        action_name = "make_payment_for_1_year"
        num_of_months = 12

        return self.render_intermediate_template(
            request, queryset, action_name, num_of_months)
    
    make_payment_for_1_year.short_description = "1 Year Plan For Top Profile"


    def make_payment(self, request, plan_desc, top_profile_reg_no, price, team_count):
        """
        Makes the requested payment
        """

        complete_payment_info = {
            "payment_method": "manual_payment",
            "request_type": "confirmation",
            "payment_info": {
                'reg_no': top_profile_reg_no,
                'amount': price,}}
        
        payment_accepted, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        
        if payment_accepted:
            self.message_user(
                request, 
                ngettext(
                    f'{plan_desc} payment for {team_count} team was successfully made.',
                    f'{plan_desc} payment for {team_count} teams was successfully made.', team_count), 
                    messages.SUCCESS)

        else:
            self.message_user(
                request,
                error_result,
                messages.ERROR)

        return HttpResponseRedirect(request.get_full_path())

    def render_intermediate_template(self, request, queryset, action_name, num_of_months):

        # We only accept 1 top profile at a time
        if queryset.count() > 1:
            self.message_user(
                request,
                "You are only allowed to make payment for 1 top profile at a time",
                messages.ERROR)

            return

        # We verify number of months
        if num_of_months == 1:
            page_subtitle = "1 Month Plan"
            num_of_months = 1

        elif num_of_months == 6:
            page_subtitle = "6 Months Plan"
            num_of_months = 6

        elif num_of_months == 12:
            page_subtitle = "1 Year Plan"
            num_of_months = 12

        else:
            self.message_user(
                request,
                "You provided a wrong number of months",
                messages.ERROR)

        top_profile = queryset[0]

        teams = EmployeeProfile.objects.filter(
                profile=top_profile).select_related('user')
                
        team_count = teams.count()

        team_user_desc = ngettext(
            f"{team_count} Team User", f"{team_count} Team Users", team_count)

        top_profile_name = f'{top_profile.user.get_full_name()} ({top_profile.user.email})'

        price = PriceGeneratorClass.all_teams_price_calc(num_of_months, team_count)

        page_data = {
            'page_subtitle': page_subtitle,
            'single_payment': False,
            'top_profile_name': top_profile_name,
            'price': price,
            'team_user_desc': team_user_desc
        }

        # All requests here will actually be of type POST 
        # so we will need to check for our special key 'make_payment' 
        # rather than the actual request type
        if 'make_payment' in request.POST:
            self.make_payment(request, page_subtitle, top_profile.reg_no, price, team_count)
            return HttpResponseRedirect(request.get_full_path())

        return render(request,
                      'admin/admin_top_user_paymement.html',
                      context={
                          'top_profiles':queryset,
                          'action_name': action_name,
                          'page_data': page_data})

        

class EmployeeProfileAdminPaymentActionMixin:

    def make_payment_for_1_month(self, request, queryset):
        """
        Creates a 1 month plan admin action
        """

        action_name = "make_payment_for_1_month"
        num_of_months = 1

        return self.render_intermediate_template(
            request, queryset, action_name, num_of_months)
    
    make_payment_for_1_month.short_description = "1 Month Plan For Team Profile"

    def make_payment_for_6_months(self, request, queryset):
        """
        Creates a 6 months plan admin action
        """

        action_name = "make_payment_for_6_months"
        num_of_months = 6

        return self.render_intermediate_template(
            request, queryset, action_name, num_of_months)
    
    make_payment_for_6_months.short_description = "6 Months Plan For Team Profile"

    def make_payment_for_1_year(self, request, queryset):
        """
        Creates a 1 year plan admin action
        """

        action_name = "make_payment_for_1_year"
        num_of_months = 12

        return self.render_intermediate_template(
            request, queryset, action_name, num_of_months)
    
    make_payment_for_1_year.short_description = "1 Year Plan For Team Profile"


    def make_payment(self, request, plan_desc, team_profile, price):
        """
        Makes the requested payment
        """

        complete_payment_info = {
            "payment_method": "manual_payment",
            "request_type": "confirmation",
            "payment_info": {
                'reg_no': team_profile.reg_no,
                'amount': price,}}

        payment_accepted, error_result = AcceptPayment(**complete_payment_info).accept_payments()

        if payment_accepted:

            team_profile_name = f'{team_profile.user.get_full_name()} ({team_profile.user.email})'
            
            self.message_user(
                request, 
                f'{plan_desc} payment for {team_profile_name} team was successfully made.', 
                messages.SUCCESS)

        else:
            self.message_user(
                request,
                error_result,
                messages.ERROR)

        return HttpResponseRedirect(request.get_full_path())

    def render_intermediate_template(self, request, queryset, action_name, num_of_months):

        # We verify number of months
        if num_of_months == 1:
            page_subtitle = "1 Month Plan"
            num_of_months = 1

        elif num_of_months == 6:
            page_subtitle = "6 Months Plan"
            num_of_months = 6

        elif num_of_months == 12:
            page_subtitle = "1 Year Plan"
            num_of_months = 12

        else:
            self.message_user(
                request,
                "You provided a wrong number of months",
                messages.ERROR)

        team_count = queryset.count()

        team_user_desc = ngettext(
            f"{team_count} Team User", f"{team_count} Team Users", team_count)

        price = PriceGeneratorClass.all_teams_price_calc(num_of_months, team_count)

        page_data = {
            'page_subtitle': page_subtitle,
            'single_payment': True,
            'price': price,
            'team_user_desc': team_user_desc
        }

        # All requests here will actually be of type POST 
        # so we will need to check for our special key 'make_payment' 
        # rather than the actual request type
        if 'make_payment' in request.POST:

            for team in queryset:

                single_price = PriceGeneratorClass.team_price_calc(num_of_months)

                self.make_payment(
                    request, 
                    page_subtitle, 
                    team, 
                    single_price)

            return HttpResponseRedirect(request.get_full_path())

        return render(request,
                      'admin/admin_team_user_paymement.html',
                      context={
                          'team_profiles':queryset,
                          'action_name': action_name,
                          'page_data': page_data})
        