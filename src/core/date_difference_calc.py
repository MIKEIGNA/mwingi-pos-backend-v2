



# This function has been tested in mylogentries tests "test_date_difference_calc.py"
def date_difference_calc(date1, date2):
    """
    Returns the duration between two dates in form of minutes or seconds if the duration is 
    shorter than a minute
    """
    
    
    try:
        
        duration = date1 - date2
        
        time_diff = divmod(duration.days * 86400 + duration.seconds, 60)
        
        minute = time_diff[0]
        seconds = time_diff[1]
        
        if minute:
            if minute == 1:
                return "{} Minute".format(minute)
            
            else:
                return "{} Minutes".format(minute)
            
        else:
            return "{} Seconds".format(seconds)
            
    except:
        return "Unknown"

            
        
    