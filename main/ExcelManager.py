import xlsxwriter

class ExcelManager:
    def __init__(self, path):
        self.workbook = xlsxwriter.Workbook(path)
        self.worksheet = self.workbook.add_worksheet()
        self.x = 0
        self.y = 0
        self.worksheet.write(self.x, self.y, "Title")
        self.worksheet.write(self.x, self.y + 1, "Date")
        self.worksheet.write(self.x, self.y + 2, "Category")
        self.worksheet.write(self.x, self.y + 3, "Picture filename")
        self.worksheet.write(self.x, self.y + 4, "Hit count")
        self.worksheet.write(self.x, self.y + 5, "Has money in title")
        self.x += 1

    
    def write_to_row(self, data):
        for i in range(len(data)):
            self.worksheet.write(self.x, i, data[i])
        self.x += 1

    def close(self):
        self.workbook.close()
        print("Excel file saved.")