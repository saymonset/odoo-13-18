{
    'name': 'Delivery Orders Report',
    'version': '1.0',
    'description': 'Delivery Orders Report',
    'summary': 'Delivery Orders Report',
    'author': 'MyCompany',
    'license': 'LGPL-3',
    'category': 'sale',
    'depends': [
        'base','sale_management','stock','product'
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/profit_margin_views.xml",
        "report/average_sales_report.xml",
        "report/delivery_category_report.xml",
        "report/delivery_order_report.xml",
        "report/profit_margin_report.xml",
        "wizard/wizard_average_sales_and_profit_margin.xml",
        "wizard/wizard_delivery_order_report.xml"
    ],
    
}