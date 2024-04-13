# traqsale-cloud


* Add accounts tasks and test them
* Add accounts admin and test
* Accounts homepage tests
* Finish billing payment tests
* Remove all supervisor or team names from the project
* Investigate receipt's get_profile. If it should return the store's profile or it's
* own profile. Do this for all projects with similar methods
* I think you should start storing firebase responses

* Change all serializer.is_valid() to serializer.is_valid(raise_exception=True)

* Starting with product_pos_serializers change all serializer reg_no fields to 
  use BigInteger instead of Integer



Changes this 'profile__user__email=self.request.user' to 
profile__user=self.request.user



Test User 
First name = Test
Last name = User
Email = testuser@gmail.com
Phone = 0718571899


Deleted all pycache files

find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf






# Add required permissons for clusters
pip install -r requirements.txt