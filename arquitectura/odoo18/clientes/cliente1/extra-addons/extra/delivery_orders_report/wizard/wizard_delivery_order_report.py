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
        print(f'SQL Result: {self.sql_result}')
        return self.env.ref('delivery_orders_report.action_report_wizard_delivery_order_report').report_action(self)
    
   
    def get_category_name(self,id):
        if not id:
            return False
        return self.env["product.category"].browse(id).name or False
 
    def deliveryOrderSql(self):
        self.env.cr.execute("""
                            SELECT
                                picking.date,
                                stock_picking_type.name AS tipo_entrega,
                                partner.name AS lugar_entrega,
                                picking.name AS folio,
                                SUM(move.product_uom_qty) AS cantidad,
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
                            WHERE
                                stock_picking_type.id =  %(type_id)s
                                --AND picking.date >= '2025-06-03 00:00:00' 
                                --AND picking.date < '2025-06-04 00:00:00'  -- Cambiado para incluir todo el día 3
                            GROUP BY
                                stock_picking_type.name,
                                partner.name,
                                picking.name,
                                picking.date,
                                productmpl.name
                            ORDER BY
                                partner.name;""", 
                                        {'type_id': 2})
        result = self.env.cr.fetchall();
        
          # Transformar el resultado SQL en un formato adecuado para el reporte
        docs_list = []  # Crear una lista temporal
        cantidadTotal= 0
        picking_type =''
        almacen =''
        dateProgrammer=''
        clave =''
        for row in result:
            docs_list.append({
                'date': row[0].strftime('%Y-%m-%d %H:%M:%S'),
                'tipo_entrega': row[1]['en_US'],
                'lugar_entrega': row[2],
                'folio': row[3],
                'cantidad': row[4],
                'nombre_producto': row[5]['en_US'],
            })
            cantidadTotal += row[4]  # Sumar la cantidad total
            picking_type = row[1]['en_US']  # Asignar el tipo de entrega
            almacen = 'Por colocar'
            dateProgrammer='por Colocar'
            clave='Porcolocar'
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
             'cantidadTotal': cantidadTotal,
             'picking_type':picking_type,
             'almacen':almacen,
             'dateProgrammer':dateProgrammer,
             'clave':clave,
            'grouped_docs': grouped_docs,
            'fechabusqueda': 'Por colocar',
            'numero':'Por colocar',
             
        }  
           # Convert the list to JSON
        return json.dumps(bodyreport)