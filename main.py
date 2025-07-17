from libs.sheets import workbook

sheets = map(lambda x: x.title, workbook.worksheets())

sheet = workbook.worksheet("Tabellenblatt1")

sheet.update_cell(1, 1, "Hello World!")

if __name__ == "__main__":
    print(list(sheets))