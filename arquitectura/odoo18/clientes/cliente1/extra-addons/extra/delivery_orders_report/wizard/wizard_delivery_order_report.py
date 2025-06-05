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
        sql_result = self.deliveryOrderSql() 
        
        return self.env.ref('delivery_orders_report.action_report_wizard_delivery_order_report').report_action(self)
    
    def get_products_line(self):
        vals = {}
        if self.group_category:
            categorys = list(set(self.sale_order_line_ids.mapped("product_template_id.categ_id.id")))
            for category in categorys:
                products = {}
                for line in self.sale_order_line_ids.filtered(lambda l:l.product_template_id.categ_id.id == category):
                    qty = line.product_uom_qty
                    cost = line.product_template_id.standard_price * qty
                    price = line.product_template_id.list_price * qty
                    # utility = price-cost
                    # porcentage = (utility)*100/(cost or 1)
                    # margin = ((utility)/(price or 1))*100
                    if line.product_template_id.id not in products:
                        products[line.product_template_id.id] = {
                            'default_code': line.product_template_id.default_code,
                            'name': line.product_template_id.name,
                            'qty': qty,
                            'cost': cost,
                            'price': price,
                            # 'utility':price-cost,
                            # 'porcentage': round(porcentage,2),
                            # 'margin': margin,
                        }
                    else:
                        products[line.product_template_id.id]["qty"] += qty
                        products[line.product_template_id.id]["cost"] += cost
                        products[line.product_template_id.id]["price"] += price
                        # products[line.product_template_id.id]["utility"] += utility
                        # products[line.product_template_id.id]["porcentage"] += round(porcentage,2)
                        # products[line.product_template_id.id]["margin"] += margin
                vals[category] = products

        else:
            products = {}
            for line in self.sale_order_line_ids:
                qty = line.product_uom_qty
                cost = line.product_template_id.standard_price * line.product_uom_qty
                price = line.price_total
                # utility = price-cost
                # porcentage = (utility)*100/(cost or 1)
                # margin = ((utility)/(price or 1))*100
                if line.product_template_id.id not in products:
                    products[line.product_template_id.id] = {
                        'default_code': line.product_template_id.default_code,
                        'name': line.product_template_id.name,
                        'qty': qty,
                        'cost': cost,
                        'price': price,
                        # 'utility':price-cost,
                        # 'porcentage': round(porcentage,2),
                        # 'margin': margin,
                    }
                else:
                    products[line.product_template_id.id]["qty"] += qty
                    products[line.product_template_id.id]["cost"] += cost
                    products[line.product_template_id.id]["price"] += price
                    # products[line.product_template_id.id]["utility"] += utility
                    # products[line.product_template_id.id]["porcentage"] += round(porcentage,2)
                    # products[line.product_template_id.id]["margin"] += margin
            vals[False] = products
        return vals

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
        for row in result:
            docs_list.append({
                'date': row[0].strftime('%Y-%m-%d %H:%M:%S'),
                'tipo_entrega': row[1]['en_US'],
                'lugar_entrega': row[2],
                'folio': row[3],
                'cantidad': row[4],
                'nombre_producto': row[5]['en_US'],
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
    
        return grouped_docs;