from corelib.Loggable import Loggable
from corelib.Constants import Constants

class Row:
    
    def __init__(self, data, color):
        
        self.data = data
        
        self.color = color

class Table(Loggable):
    
    def __init__(self):
        
        super().__init__(__name__)
        
        self.__column_widths = []
        self.__rows = []
        
    def add_row(self, row, color=None):
        
        self.__rows = [Row(row, color)]    
        self.print()
        
        
    def set_column_widths(self, column_widths):
        
        self.__column_widths = column_widths
        
    def print(self):
        # for index, row in enumerate(self.__rows): 
        #     self.log.info(row.data)
        
        for index, row in enumerate(self.__rows):   
            data = row.data
            ci = 0
            
            header_str = []
            column_str = []            
            for column in data:
                length = len(column)
                blanks = self.__column_widths[ci] - length             
                
            #     if index.__eq__(0):
            #         header_str.append(column + ' ' * blanks) 
            #     else:
            #         column_str.append(column + ' ' * blanks)
            #     ci += 1
                if index.__eq__(0):
                    header_str.append(column + ' ' * blanks) 
                column_str.append(column + ' ' * blanks)
                ci += 1

            # header = '|'.join(header_str)
            # content = '|'.join(column_str)
            content = '|'.join(column_str)

            if row.color is not None:
                content = Constants.colorize(content, row.color)

            Loggable.print_raw(content)
            
            # if row.color is not None:
            #     content = Constants.colorize(content, row.color)
            # # if index.__eq__(0):
            #     # Loggable.print_raw(header)            
            # Loggable.print_raw(content)    