curl -X POST http://localhost:8000/karwai \
        -F "bankStatement=@getjobid4620060.pdf" \
        -F "companyData=@assets_dev/test_company.xlsx" \
        -F "formatType=debit-plus-credit" \
        -F "transactionDateColumn=Posting Date" \
        -F "transactionDetailsColumn=Remarks" \
        -F "debitPlusCreditColumn=Deb./Cred. (LC)" \
        -F "sheetName=May-26"