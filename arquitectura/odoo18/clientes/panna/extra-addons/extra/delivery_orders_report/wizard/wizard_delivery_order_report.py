from odoo import models, fields, api
from .delivery_category_group import DeliveryCategoryGroup
from .delivery_order_group import DeliveryOrerGroup


class WizardDeliveryOrder(models.TransientModel):
    _name = "wizard.delivery.order.report"
    _description = "Wizard Informe de Órdenes de Entrega"

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
            self.sql_result = DeliveryCategoryGroup.delivery_category_group(self);
            return self.env.ref('delivery_orders_report.action_report_wizard_delivery_category_report').report_action(self)
            report_template_delivery_category
        else:
            print("Agrupar por Orden de entrega")
            self.sql_result = DeliveryOrerGroup.delivery_order_group(self)
            return self.env.ref('delivery_orders_report.action_report_wizard_delivery_order_report').report_action(self)
    
   
    def get_category_name(self,id):
        if not id:
            return False
        return self.env["product.category"].browse(id).name or False
  
    
     
  