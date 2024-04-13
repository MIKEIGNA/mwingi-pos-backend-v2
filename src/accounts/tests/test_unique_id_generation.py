from core.test_utils.custom_testcase import TestCase
from core.reg_no_generator import GetUniqueId


class GetUniqueIdTestCase(TestCase):
    def test_if_GetUniqueId_can_accept_value1_only(self):
        
        value1 = 5
        
        reg_no = GetUniqueId(value1).get_unique_id() 
        
        self.assertEqual(type(reg_no), int)
        
    def test_if_GetUniqueId_can_accept_value1_and_value2_only(self):
        
        value1 = 5
        value2 = 15
        
        reg_no = GetUniqueId(value1, value2).get_unique_id() 
        
        self.assertEqual(type(reg_no), int)
        
    def test_if_GetUniqueId_t_type_is_minutes(self):
        
        value1 = 5
        value2 = 15
        
        reg_no = GetUniqueId(value1, value2, 'minutes').get_unique_id() 
        
        self.assertEqual(type(reg_no), int)
        
    def test_if_GetUniqueId_t_type_is_seconds(self):
        
        value1 = 5
        value2 = 15
        
        reg_no = GetUniqueId(value1, value2, 'seconds').get_unique_id() 
        
        self.assertEqual(type(reg_no), int)
        
    def test_if_GetUniqueId_t_type_is_micros(self):
        
        value1 = 5
        value2 = 15
        
        reg_no = GetUniqueId(value1, value2, 'micros').get_unique_id() 
        
        self.assertEqual(type(reg_no), int)
        
    def test_for_failure_if_GetUniqueId_t_type_is_wrong(self):
        
        value1 = 5
        value2 = 15
        
        reg_no = GetUniqueId(value1, value2, 'wrongarg').get_unique_id() 
        
        self.assertEqual(reg_no, False )
        

