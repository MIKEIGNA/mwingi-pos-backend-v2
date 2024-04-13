import json
import csv

from os import path

class FileReader():
    """Opens a file and reads all the content."""
    
    def __init__(self, file_path, read_from):
        
        filepath = path.realpath(file_path)
        self.read_from = filepath + read_from
            
    def openfile(self,filename):
        
        with open(filename) as f:
            text = f.read()
            f.close()
            
        return text
    
    def emptyfile(self):
        """ Write youtube links file """
        
        write_to = self.read_from
        content = ''
    
        with open(write_to, 'w') as f:
            f.write(content)
            f.close()
    
    def get_file_content(self):
        content = str(self.openfile(self.read_from))
        content = content.split('\n')
        content = list(filter(None, content)) #Remove Empty lines from text
        
        return content

class LogReader():
    def __init__(self, string, delimiter=' ', quotechar='"'):
        self.string = string
        self.delimiter = delimiter
        self.quotechar = quotechar
        
    def read_line(self):
        reader = csv.reader(self.string, delimiter=self.delimiter , quotechar=self.quotechar)
        
        listo = []
        for line in reader:
            listo.append(line)
            
        return listo
    
    def get_list(self):
        string = ''
        for line in self.read_line():
            if line == ['', '']:
                string+='...'
            else:
                string+=line[0]
                
        new_string = string.split('...')
        
        return new_string
    
class LogMap():
    def __init__(self, log_list):
        self.log_list = log_list
        
    def get_dict(self):
        data = {'date':self.log_list[0],
                'time':self.log_list[1],
                'ip':self.log_list[2],
                'meta_user':self.log_list[3],
                'user':self.log_list[4],
                'method':self.log_list[5].split(' ')[0],
                'full_path':self.log_list[5].split(' ')[1],
                'status_code':self.log_list[6],
                'content_length':self.log_list[7],
                'process':self.log_list[8],
                'referer':self.log_list[9],
                'user_agent':self.log_list[10],
                'port':self.log_list[11],
                'response_time':self.log_list[12]
                }
        
        return data
        
    
class LogDict():
    def __init__(self, string):
        self.string = string
        
    def get_dict(self):
        log_list = LogReader(self.string).get_list()
        data = LogMap(log_list).get_dict()
        
        return data
        
        
def get_log_content():
    content = FileReader('xlogs', '/test_page_views.log').get_file_content()
    
    
    listo = []
    for line in content:  
        data = LogDict(line).get_dict()
        listo.append(data)
    
    
    return listo

def get_test_firebase_sender_log_content(only_include = None):
    content = FileReader('xlogs', '/test_firebase_sender.log').get_file_content()

    """
    Args:
        only_include: (list) If provided, only payloads with model names that 
        are in this list will be returned
    """

    listo = []
    for line in content:

        line = line[20:]  # Remove log date
        dico = json.loads(line)

        # Since firebase will error out when we pass in Decimal values, we ensure
        # that only string values are passed
        for k, v in dico['payload'].items():

            if type(v) is not str:
                raise Exception(f"{k} must be a str")

        if only_include:
            if dico['payload']['model'] in only_include:
                listo.append(dico)
        else:
            listo.append(dico) 
    
    return listo

