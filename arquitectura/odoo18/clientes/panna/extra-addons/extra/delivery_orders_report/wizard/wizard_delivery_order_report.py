from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
from datetime import datetime

class WizardDeliveryOrder(models.TransientModel):
    _name = "wizard.delivery.order.report"
    _description = "Wizard Informe de Órdenes de Entrega"

    name = fields.Char("Nombre")
    date_from = fields.Date("Desde Fecha Programada")
    date_to = fields.Date("Hasta Fecha Programada")
    warehouse_ids = fields.Many2many("stock.warehouse",string="Almacén")
    place_of_delivery_ids = fields.Many2many("res.partner",string="Lugar de Entrega")
    stock_picking_type_ids = fields.Many2many("stock.picking.type",string="Tipo de Entrega")
    
    sale_order_line_ids = fields.Many2many("sale.order.line",string="Lineas")
    group_category = fields.Boolean("Agrupar por Categoria")
    sql_result = fields.Json("SQL Result")  # Define sql_result as a JSON fiel
    def print_report(self):

        ##lines = self.env["sale.order.line"].search(domain)        
        self.sql_result = self.deliveryOrderSql();
      #  print("------------------0--------------------------");
       # print("SQL Result:", self.sql_result)  # Debugging line to check the SQL result
       # print("------------------1--------------------------");
        return self.env.ref('delivery_orders_report.action_report_wizard_delivery_order_report').report_action(self)
    
   
    def get_category_name(self,id):
        if not id:
            return False
        return self.env["product.category"].browse(id).name or False
 
    def deliveryOrderSql(self):
        pickingTypeId = None  # Cambiado a None
        placeOfDeliveryId = None  # Cambiado a None

        # if not self.date_from:
        #     raise ValidationError("Desde Fecha Requerido")
        
        # if self.date_to:
        #     print(f"Fecha Hasta Requerido {self.date_to}")
        
        if self.place_of_delivery_ids:
            for place_of_delivery in self.place_of_delivery_ids:
                placeOfDeliveryId = place_of_delivery.id
        
        if self.stock_picking_type_ids:
            for picking_type in self.stock_picking_type_ids:
                pickingTypeId = picking_type.id

        # Inicializar la consulta SQL y los parámetros
        query = """
            SELECT
                TO_CHAR(picking.date, 'DD/MM/YYYY'),
                stock_picking_type.name AS titlehead,
                stock_location.name AS almacenhead,
                TO_CHAR(picking.scheduled_date, 'DD/MM/YYYY') AS fechaprogramadaheaad,
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
            LEFT JOIN
                res_partner AS partner ON partner.id = picking.partner_id  
            JOIN
                stock_picking_type AS stock_picking_type ON stock_picking_type.id = picking.picking_type_id      
            JOIN
                stock_location ON stock_location.id = picking.location_id  
            WHERE
                (stock_picking_type.id = %(type_id)s OR %(type_id)s IS NULL)
                AND (partner.id = %(place_id)s OR %(place_id)s IS NULL)
        """

        # Inicializar la lista de parámetros
        params = {
            'type_id': pickingTypeId,
            'place_id': placeOfDeliveryId
        }

        # Agregar condiciones de fecha si están disponibles
        if self.date_from:
            query += " AND picking.date >= %(date_from)s"
            params['date_from'] = self.date_from

        if self.date_to:
            query += " AND picking.date < %(date_to)s"
            params['date_to'] = self.date_to

        query += """
            GROUP BY
                stock_picking_type.name,
                partner.name,
                picking.origin,
                picking.date,
                productmpl.name,
                stock_location.name,
                TO_CHAR(picking.scheduled_date, 'DD/MM/YYYY')
            ORDER BY
                TO_CHAR(picking.scheduled_date, 'DD/MM/YYYY'),
                partner.name;
        """
        
        print("SQL Query:", query)  # Debugging line to check the SQL query
        print("SQL Params:", params)
        print("-----")
        # Ejecutar la consulta
        self.env.cr.execute(query, params)
        
        result = self.env.cr.fetchall()

        
          # Transformar el resultado SQL en un formato adecuado para el reporte
        docs_list = []  # Crear una lista temporal
        almacenhead =''
        fechaprogramadaheaad=''
        # Crear un diccionario para agrupar por lugar_entrega
        lugarEntregaFirstTime = {}
        titlehead = ''
        nombre_producto = ''
        for row in result:
            titlehead = self.obtener_titulo(row[1])  
            nombre_producto = self.obtener_titulo(row[7])  
            
            almacenhead = row[2]
            fechaprogramadaheaad=row[3]
            lugar_entrega = row[4];
            if lugar_entrega  in lugarEntregaFirstTime:
                lugar_entrega = ''
            
            
            # ciclo de registros        
            docs_list.append({
                'lugar_entrega_key': row[4],
                'lugar_entrega': lugar_entrega,
                'folio': row[5],
                'cantidad': row[6],
                'nombre_producto': nombre_producto,
            })
            if lugar_entrega:
               if lugar_entrega not in lugarEntregaFirstTime:
                  lugarEntregaFirstTime[lugar_entrega] = True
            
        
            
        # Ordenar por lugar_entrega_key en la lista original
        docs_list.sort(key=lambda x: (x['lugar_entrega_key'], x['lugar_entrega'] or ''))
        bodyreport = {
             'titlehead':titlehead,
             'almacenhead':almacenhead,
             'fechaprogramadaheaad':fechaprogramadaheaad,
            'docs_list': docs_list,  # Agregar el arreglo de claves y valores
        }  
           # Convert the list to JSON
        return json.dumps(bodyreport)
    
    
    def obtener_titulo(self,titleheadKeyValue):
        titleHead = ''  # Inicializar titleHead

        # Obtener un valor sin conocer la clave
        for valor in titleheadKeyValue.values():
            if valor:  # Verificar que el valor no esté vacío
                titleHead = valor
                break  # Salir del bucle una vez que se encuentra el primer valor no vacío

        return titleHead  # Devolver el tipo de entrega