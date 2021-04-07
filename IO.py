import csv

class CSVFiles:

    def __init__(self, file_name):
        self.filename = file_name

    def SefFileName(self, file_name):
        self.filename = file_name

    def SetCSVFieldName(self, field):
        self.fieldnames = field

    def GetCSVFieldName(self):
        return self.fieldnames

    def WriteHeader(self):
        try:
            with open(self.filename, 'w', newline='') as csvf:
                writer = csv.DictWriter(csvf, fieldnames=self.fieldnames)
                writer.writeheader()
        except IOError as e:
            print("CSV File not open!")

    def WriteRow(self, row_values):
        if len(row_values) > len(self.fieldnames):
            return
        res_dct = {self.fieldnames[i]: row_values[i] for i in range(0, len(self.fieldnames), 1)}
        try:
            with open(self.filename, 'a', newline='') as csvf:
                writer = csv.DictWriter(csvf, fieldnames=self.fieldnames)
                writer.writerow(res_dct)
        except IOError as e:
            print("CSV File not open!")
        except ValueError as e:
            print(e)

    def WriteRows(self, row_values):
        res_dct = []
        for row in row_values:
            res_dct.append({self.fieldnames[i]: row[i] for i in range(0, len(self.fieldnames), 1)})
        try:
            with open(self.filename, 'a', newline='') as csvf:
                writer = csv.DictWriter(csvf, fieldnames=self.fieldnames)
                writer.writerows(res_dct)
        except IOError as e:
            print("CSV File not open!")
        except ValueError as e:
            print(e)

class WritePrintToFile():
    @staticmethod
    def Write(obj):
        sourceFile = open('info.txt', 'a')
        print(obj, file=sourceFile)
        sourceFile.close()
