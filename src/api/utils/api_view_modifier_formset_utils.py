from products.models import Modifier, ModifierOption

class ApiPosModifierFormestHelpers:

    @staticmethod
    def validate_pos_modifiers(modifiers_info, store):
        """
        Collects the modifiers from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            modifiers_info --> A list of modifier's reg_no's that should be verified
            store (Store) --> Store used to verify modifiers
        """

        collected_modifiers = []
        for info in modifiers_info:
        
            try:
                reg_no = info.get('reg_no', None)

                if reg_no:

                    collected_modifiers.append(
                        Modifier.objects.get(stores__id=store.id, reg_no=reg_no).id
                    )
            except: # pylint: disable=bare-except
                # Log here
                return False
    
        return collected_modifiers

    @staticmethod
    def add_or_remove_modifiers(model, collected_modifiers):
        """
        Adds or removes modifiers from the passed model

        Parameters:
            model --> A model with a modifiers field(ManyToMany)
            collected_modifiers --> A list of modifiers id from view
        """
        query = model.modifiers.all().values_list('id')

        current_modifiers = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_modifiers)):
            if not collected_modifiers[i] in current_modifiers:
                list_to_be_added.append(collected_modifiers[i])


        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_modifiers)):
            if not current_modifiers[i] in collected_modifiers:
                list_to_be_removed.append(current_modifiers[i])

        model.modifiers.add(*list_to_be_added)
        model.modifiers.remove(*list_to_be_removed)


class ApiWebModifierFormestHelpers:

    @staticmethod
    def validate_web_modifiers(modifiers_info, profile):
        """
        Collects the modifiers from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            modifiers_info --> A list of modifier's reg_no's that should be verified
            profile (Profile) --> Profile used to verify modifiers
        """

        collected_modifiers = []
        for info in modifiers_info:
        
            try:
                reg_no = info.get('reg_no', None)

                if reg_no:

                    collected_modifiers.append(
                        Modifier.objects.get(profile=profile, reg_no=reg_no).id
                    )
            except: # pylint: disable=bare-except
                # Log here
                return False
    
        return collected_modifiers

    @staticmethod
    def add_or_remove_modifiers(model, collected_modifiers):
        """
        Adds or removes modifiers from the passed model

        Parameters:
            model --> A model with a modifiers field(ManyToMany)
            collected_modifiers --> A list of modifiers id from view
        """
        if not type(collected_modifiers) == list:
            return

        query = model.modifiers.all().values_list('id')

        current_modifiers = [x[0] for x in query]

        # List to be added
        list_to_be_added = []

        for i in range(len(collected_modifiers)):
            if not collected_modifiers[i] in current_modifiers:
                list_to_be_added.append(collected_modifiers[i])


        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_modifiers)):
            if not current_modifiers[i] in collected_modifiers:
                list_to_be_removed.append(current_modifiers[i])

        model.modifiers.add(*list_to_be_added)
        model.modifiers.remove(*list_to_be_removed) 
        
class ApiModifierOptionsFormestHelpers:

    @staticmethod
    def update_modifier_options(options_info, modifier):
        """
        Collects the options from the passed data and then updates modifier's
        options values

        Parameters:
            options_info --> A list of options's data that should be verified
            store (Store) --> Store used to verify modifiers
        """
        collected_options_reg_nos = []
        new_options_info = []
        for info in options_info:

            # This info will be used later to create/delete models
            if info['reg_no'] == 0:
                new_options_info.append(info)

                continue
            else:
                collected_options_reg_nos.append(info['reg_no'])

            if info.get('is_dirty', None):

                try:

                    ModifierOption.objects.filter(
                        reg_no=info['reg_no'], modifier=modifier
                    ).update(
                        name=info['name'], price=info['price'],
                    )

                except: # pylint: disable=bare-except
                    " Log here"
                    return False


        # Delete options that are not in the collected_options_reg_nos
        saved_options = modifier.modifieroption_set.all().values_list('reg_no')
        for opt in saved_options:
            if not opt[0] in collected_options_reg_nos:
                ModifierOption.objects.filter(reg_no=opt[0]).delete()

        # Create the newly added options
        for info in new_options_info:
            ModifierOption.objects.create(
                modifier=modifier,
                name=info['name'],
                price=info['price'],
            )
        
        return True
class ApiWebEmployerrModifierFormestHelpers:

    @staticmethod
    def validate_web_modifiers_for_employee(modifiers_info, employee_profile):
        """
        Collects the modifiers from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            modifiers_info --> A list of modifier's reg_no's that should be verified
            profile (Profile) --> Profile used to verify modifiers
        """

        collected_modifiers = []
        for info in modifiers_info:
        
            try:
                reg_no = info.get('reg_no', None)

                if reg_no:

                    collected_modifiers.append(
                        Modifier.objects.get(
                            stores__employeeprofile=employee_profile, 
                            reg_no=reg_no
                        ).id
                    )
            except: # pylint: disable=bare-except
                # Log here
                return False
    
        return collected_modifiers

    @staticmethod
    def add_or_remove_modifiers(model, collected_modifiers):
        """
        Adds or removes modifiers from the passed model

        Parameters:
            model --> A model with a modifiers field(ManyToMany)
            collected_modifiers --> A list of modifiers id from view
        """
        if not type(collected_modifiers) == list:
            return

        query = model.modifiers.all().values_list('id')

        current_modifiers = [x[0] for x in query]

        # List to be added
        list_to_be_added = []

        for i in range(len(collected_modifiers)):
            if not collected_modifiers[i] in current_modifiers:
                list_to_be_added.append(collected_modifiers[i])


        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_modifiers)):
            if not current_modifiers[i] in collected_modifiers:
                list_to_be_removed.append(current_modifiers[i])

        model.modifiers.add(*list_to_be_added)
        model.modifiers.remove(*list_to_be_removed)
        