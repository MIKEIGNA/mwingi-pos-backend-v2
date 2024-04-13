from rest_framework.authtoken.models import Token


    
def logout_api(user):
    """
    Regenerates user's token
    """
    
    # Delete user token
    Token.objects.get(user=user).delete()
        
    # Create a new token for user
    Token.objects.get_or_create(user=user)
    
    
def logout_web(user):
    """
    'Delete user's sessions
    """
    from accounts.models import UserSession
    
    user_sessions = UserSession.objects.filter(user = user)

    for user_session in user_sessions:
        user_session.session.delete()
        
        
def logout_user_everywhere(user):
    """
    # When a web user logs out:
        user's web sessions are deleted
        user's api token is regenerated
        
    # When a web user changes password:
        user's web sessions are deleted 
        user's api token is regenerated
    
    # When an api user logs out:
        user's web sessions might not be deleted ** This is cannot be depended upon 
        user's api token is regenerated
        
    # When an api user changes password:
        user's web sessions are deleted 
        user's api token is regenerated
    """
    
    try:
        logout_web(user)
        logout_api(user)
    except:
        pass
    