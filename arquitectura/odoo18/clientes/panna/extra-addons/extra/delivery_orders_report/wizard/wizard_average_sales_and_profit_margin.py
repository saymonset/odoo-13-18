from odoo import models, fields, api
from .repository.delivery_category_group import DeliveryCategoryGroup
from  .repository.delivery_order_group import DeliveryOrerGroup


class WizardDeliveryOrder(models.TransientModel):
    _name = "wizard.average.sales.and.profit.margin"
    _description = "Informe Promedio de Ventas y Margen de Ganancias"

    name = fields.Char("Nombre")
    scheduled_date = fields.Date("Fecha Programada")
   # date_to = fields.Date("Hasta Fecha Programada")
    warehouse_ids = fields.Many2many("stock.warehouse",string="Almacén")
    place_of_delivery_ids = fields.Many2many("res.partner",string="Lugar de Entrega")
    stock_picking_type_ids = fields.Many2many("stock.picking.type",string="Tipo de Transferencia")
    # Este es la ubicación de origen del almacén
    stock_locations_ids = fields.Many2many("stock.location",string="Almacen de Origen")
    group_category = fields.Boolean("Agrupar por Categoria")
                           
                       

    
    sale_order_line_ids = fields.Many2many("sale.order.line",string="Lineas")
    group_category = fields.Boolean("Agrupar por Categoria")
    sql_result = fields.Json("SQL Result")  # Define sql_result as a JSON fiel
    
    def print_report(self):
        if self.group_category:
            print("Agrupar por Categoria")
            # self.sql_result = DeliveryCategoryGroup.delivery_category_group(self);
            # return self.env.ref('delivery_orders_report.action_average_sales_report').report_action(self)
           # report_template_delivery_category
            return {
                'type': 'ir.actions.act_window',
                'name': 'Profit Margin Report',
                'res_model': 'profit_margin',  # Cambia esto al modelo correcto
                'view_mode': 'form',
                'target': 'current',  # Cambia a 'new' si deseas abrir en una nueva ventana
            }
        else:
            print("Agrupar por Orden de entrega")
            self.sql_result = DeliveryCategoryGroup.delivery_category_group(self);
            return self.env.ref('delivery_orders_report.action_profit_margin_report').report_action(self)
    
   
    
     
    @api.onchange('group_category')        
    def on_group_category_go(self):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Profit Margin Report',
                'res_model': 'profit_margin',  # Cambia esto al modelo correcto
                'view_mode': 'form',
                'target': 'current',  # Cambia a 'new' si deseas abrir en una nueva ventana
            }
  
    
     
  