from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
from datetime import datetime

class WizardDeliveryOrder(models.TransientModel):
    _name = "wizard.delivery.order.report"
    _description = "Wizard Informe de Órdenes de Entrega"

    name = fields.Char("Nombre")
    date_from = fields.Date("Desde Fecha")
    date_to = fields.Date("Hasta Fecha")
    warehouse_ids = fields.Many2many("stock.warehouse",string="Almacén")
    sale_order_line_ids = fields.Many2many("sale.order.line",string="Lineas")
    group_category = fields.Boolean("Agrupar por Categoria")
    sql_result = fields.Json("SQL Result")  # Define sql_result as a JSON fiel
    def print_report(self):
        if not self.date_from:
            raise ValidationError("Desde Fecha Requerido")
        domain = [('display_type','=',False),('product_template_id','!=',False),('invoice_status','=','invoiced'),('order_id.date_order','>=',self.date_from)]
        if self.date_to:
            domain.append(('order_id.date_order','<=',self.date_to))
        if self.warehouse_ids:
            domain.append(('warehouse_id','in',self.warehouse_ids.ids))

        lines = self.env["sale.order.line"].search(domain)        
        self.sale_order_line_ids = lines     
        self.sql_result = self.deliveryOrderSql() 
        
        return self.env.ref('delivery_orders_report.action_report_wizard_delivery_order_report').report_action(self)
    
   
    def get_category_name(self,id):
        if not id:
            return False
        return self.env["product.category"].browse(id).name or False
 
    def deliveryOrderSql(self):
        self.env.cr.execute("""
                            SELECT
                                    TO_CHAR(picking.date, 'DD/MM/YYYY'),
                                    stock_picking_type.name AS titlehead,
                                    stock_location.name AS almacenhead,
                                    TO_CHAR(picking.scheduled_date, 'DD/MM/YYYY') AS fechaprogramadaheaad,  -- Formato de fecha
                                    partner.name AS lugar_entrega,
                                    picking.origin AS folio,
                                    SUM(move.quantity) AS cantidad,
                                    productmpl.name AS nombre_producto
                            FROM
                                stock_picking AS picking
                            JOIN
                                stock_move AS move ON move.picking_id = picking.id
                            JOIN
                                product_product AS product ON product.id = move.product_id
                            JOIN
                                product_template AS productmpl ON productmpl.id = product.product_tmpl_id
                            JOIN
                                res_partner AS partner ON partner.id = picking.partner_id  
                            JOIN
                                stock_picking_type AS stock_picking_type ON stock_picking_type.id = picking.picking_type_id      
                            JOIN
                                stock_location ON stock_location.id = picking.location_id  
                            WHERE
                                stock_picking_type.id =  %(type_id)s
                                --AND picking.date >= '2025-06-03 00:00:00' 
                                --AND picking.date < '2025-06-04 00:00:00'  -- Cambiado para incluir todo el día 3
                            GROUP BY
                                stock_picking_type.name,
                                partner.name,
                                picking.origin,
                                picking.date,
                                productmpl.name,
                                stock_location.name,
                                TO_CHAR(picking.scheduled_date, 'DD/MM/YYYY')  -- Agrupar por la fecha formateada
                            ORDER BY
                                TO_CHAR(picking.scheduled_date, 'DD/MM/YYYY'),  -- Ordenar por la fecha formateada
                                partner.name;""", 
                                        {'type_id': 2})
        result = self.env.cr.fetchall();
        
          # Transformar el resultado SQL en un formato adecuado para el reporte
        docs_list = []  # Crear una lista temporal
        titlehead =''
        almacenhead =''
        fechaprogramadaheaad=''
        for row in result:
            #En el titulo tenemos {"en_US","Delivery Orders"} y debemos sacar solo el valor que 
            # es delivery orders
            titleheadKeyValue = row[1]  # Asignar el tipo de entrega
            titleHead = titleheadKeyValue  # Asignar el tipo de entrega
            # Obtener un valor sin conocer la clave
            for valor in titleheadKeyValue.values():
                if valor:
                    titleHead=valor
            titlehead = titleHead  # Asignar el tipo de entrega
            almacenhead = row[2]
            fechaprogramadaheaad=row[3]
            # ciclo de registros        
            docs_list.append({
                'lugar_entrega': row[4],
                'folio': row[5],
                'cantidad': row[6],
                'nombre_producto': row[7],
            })
            
         # Crear un diccionario para agrupar por lugar_entrega
        grouped_docs = {}
        # Iterar sobre cada documento en docs_list
        for doc in docs_list:
            # Obtener el lugar de entrega del documento actual
            lugar_entrega = doc['lugar_entrega']
            # Verificar si el lugar de entrega ya está en el diccionario
            if lugar_entrega not in grouped_docs:
                # Si no está, inicializar una lista vacía para ese lugar de entrega
                grouped_docs[lugar_entrega] = []
            
            # Agregar el documento actual a la lista correspondiente en el diccionario
            grouped_docs[lugar_entrega].append(doc)
        bodyreport = {
             'titlehead':titlehead,
             'almacenhead':almacenhead,
             'fechaprogramadaheaad':fechaprogramadaheaad,
            'grouped_docs': grouped_docs,
        }  
           # Convert the list to JSON
        return json.dumps(bodyreport)