

class APIError(Exception):
    '''
    The base exception class for all App Annie errors.
    it contains 3 parts:
    code
    message
    traceback
    '''

    def __init__(self, code, message):
        self.code = code
        self.message_s = message
        super(APIError, self).__init__(message)

    
    
