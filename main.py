import json
import os
os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen
from datetime import datetime
from datetime import datetime, timedelta
from collections import Counter


from kivymd.app import MDApp
from kivymd.uix.label import MDLabel


class ProductoLabel(Label):
    def __init__(self, **kwargs):
        self.index = kwargs.pop('index', None)
        super().__init__(**kwargs)


class InventarioApp(MDApp):
    ARCHIVO_INVENTARIO = "inventario.json"
    ARCHIVO_VENTAS = "ventas.json" 
    # Colores pastel y fondo blanco
    COLOR_FONDO = get_color_from_hex("#E3C3FA")
    COLOR_BOTON = get_color_from_hex("#632B4F")
    COLOR_TEXTO_BOTON = get_color_from_hex("#FFFFFF")
    COLOR_TEXTO = get_color_from_hex("#9B0857")
    COLOR_ERROR = get_color_from_hex("#E63946")
   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inventario = self.cargar_inventario()
        self.historial_ventas = [] 
        
    def build(self):
       
        self.producto_seleccionado = None

        self.sm = ScreenManager()
        self.menu_screen = Screen(name='menu')
        
        self.sm.add_widget(PantallaVenta(app=self, name='venta'))

        # ===== Pantalla de menú principal =====
        self.menu_screen = Screen(name='menu')
        layout_menu = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))

        with layout_menu.canvas.before:
            Color(*self.COLOR_FONDO)
            self.rect_menu = Rectangle(size=layout_menu.size, pos=layout_menu.pos)
        layout_menu.bind(size=self._update_menu_rect, pos=self._update_menu_rect)

        btn_venta = Button(text="Iniciar venta", size_hint=(1, None), height=dp(60),
                       background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON,
                       on_press=lambda x: setattr(self.sm, 'current', 'venta'))
        btn_inventario = Button(text="Inventario", size_hint=(1, None), height=dp(60),
                            background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON,
                            on_press=lambda x: setattr(self.sm, 'current', 'inventario'))
        btn_corte = Button(text="Corte de caja", size_hint=(1, None), height=dp(60),
                       background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON,
                       on_press=lambda x: setattr(self.sm, 'current', 'corte'))

        layout_menu.add_widget(btn_venta)
        layout_menu.add_widget(btn_inventario)
        layout_menu.add_widget(btn_corte)

        self.menu_screen.add_widget(layout_menu)
        self.sm.add_widget(self.menu_screen)

        # ===== Pantalla de inventario =====
        self.inventario_screen = Screen(name='inventario')
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(0))

        with self.main_layout.canvas.before:
            Color(*self.COLOR_FONDO)
            self.rect = Rectangle(size=self.main_layout.size, pos=self.main_layout.pos)
        self.main_layout.bind(size=self._update_rect, pos=self._update_rect)

        # Agregar widgets al layout
        btn_volver = Button(text="Volver al menú", size_hint=(1, None), height=dp(40),
                        background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON,
                        on_press=lambda x: setattr(self.sm, 'current', 'menu'))
        self.main_layout.add_widget(btn_volver)

        self.btn_mostrar_formulario = Button(
            text="Agregar producto",
            size_hint=(1, None),
            height=dp(50),
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON,
            on_press=self.toggle_formulario
        )
        self.main_layout.add_widget(self.btn_mostrar_formulario)

        btns_layout = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(10))
        self.btn_eliminar = Button(
            text="Eliminar producto",
            disabled=True,
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON,
            on_press=self.eliminar_producto
        )
        btns_layout.add_widget(self.btn_eliminar)
        self.main_layout.add_widget(btns_layout)
        self.btn_editar = Button(
            text="Editar producto",
            disabled=True,
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON,
            on_press=self.editar_producto
        )
        btns_layout.add_widget(self.btn_editar)
        self.inventario_scroll = ScrollView(size_hint=(1, 1))
        self.inventario_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(10), padding=dp(5))
        self.inventario_list.bind(minimum_height=self.inventario_list.setter('height'))
        self.inventario_scroll.add_widget(self.inventario_list)
        
        self.main_layout.add_widget(self.inventario_scroll)
        if self.main_layout.parent is None:
            self.inventario_screen.add_widget(self.main_layout)

       
        self.sm.add_widget(self.inventario_screen)

        # Pantallas vacías para ahora
        self.pantalla_corte = Screen(name='corte')
        layout_corte = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        with layout_corte.canvas.before:
            Color(*get_color_from_hex("#FFF0F5"))

            self.fondo_rect = Rectangle(size=layout_corte.size, pos=layout_corte.pos)
        layout_corte.bind(size=self._actualizar_fondo_rect, pos=self._actualizar_fondo_rect)
        # Título
        layout_corte.add_widget(Label(text="Corte de Caja", font_size=24, size_hint=(1, None), height=dp(40), color=self.COLOR_TEXTO))
        # Fecha específica
        self.selector_fecha = TextInput(hint_text="YYYY-MM-DD para corte diario", size_hint=(1, None), height=dp(40))
        
        layout_corte.add_widget(self.selector_fecha)
        # Botones
        botones = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        botones.bind(minimum_height=botones.setter('height'))  # hace que crezca con el contenido
        btns = [
            Button(text="Ver estadísticas", background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON, on_press=self.ver_estadisticas),
            Button(text="Corte Diario", background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON, on_press=self.calcular_corte_diario_por_input),
            Button(text="Últimos 7 días", background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON, on_press=self.ver_corte_semanal),
            Button(text="Últimos 30 días", background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON, on_press=self.ver_corte_mensual)
        ]
        for btn in btns:
            btn.size_hint_y = None
            btn.height = dp(40)
            botones.add_widget(btn)

        layout_corte.add_widget(botones)

            
       
        # Resultado
        self.lbl_corte_resultado = Label(text="Selecciona una opción", size_hint=(1, 1), color=self.COLOR_TEXTO)
        layout_corte.add_widget(self.lbl_corte_resultado)

        # Botón volver
        btn_volver = Button(text="Volver al menú", size_hint=(1, None), height=dp(40), background_color=self.COLOR_BOTON, color=self.COLOR_TEXTO_BOTON, on_press=lambda x: setattr(self.sm, 'current', 'menu'))
        layout_corte.add_widget(btn_volver)
       

        


        self.crear_formulario()
        self.cargar_inventario()
        self.mostrar_inventario()
        self.cargar_ventas()
        self.sm.current = 'menu'
        self.pantalla_corte.add_widget(layout_corte)
        self.sm.add_widget(self.pantalla_corte)
        return self.sm
 

   
    def _actualizar_fondo_rect(self, instance, value):
        self.fondo_rect.pos = instance.pos
        self.fondo_rect.size = instance.size 
    def _update_menu_rect(self, instance, value):
        self.rect_menu.pos = instance.pos
        self.rect_menu.size = instance.size

        self.inventario = []
        self.producto_seleccionado = None

      

        # Fondo blanco
        with self.main_layout.canvas.before:
            Color(*self.COLOR_FONDO)
            self.rect = Rectangle(size=self.main_layout.size, pos=self.main_layout.pos)
        self.main_layout.bind(size=self._update_rect, pos=self._update_rect)

       

        self.crear_formulario()
        self.formulario_popup = None

        self.cargar_inventario()
        self.mostrar_inventario()

        return self.main_layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def crear_formulario(self):
        self.form_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint=(1, None))
        with self.form_layout.canvas.before:
            Color(*get_color_from_hex("#FFF0F5"))  # Un rosa claro pastel, por ejemplo

            self.form_rect = Rectangle(size=self.form_layout.size, pos=self.form_layout.pos)
        self.form_layout.bind(size=self._update_form_rect, pos=self._update_form_rect)

        
        self.form_layout.height = dp(450)

        self.input_nombre = TextInput(hint_text="Nombre producto", multiline=False)
        self.input_costo = TextInput(hint_text="Costo total (compra)", multiline=False, input_filter='float')
        self.input_piezas = TextInput(hint_text="Número de piezas", multiline=False, input_filter='int')

        self.btn_calcular_sugerido = Button(
            text="Calcular precio sugerido",
            size_hint=(1, None),
            height=dp(40),
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON
        )
        self.btn_calcular_sugerido.bind(on_press=self.calcular_precio_sugerido)

        self.lbl_precio_sugerido = Label(
            text="Precio sugerido: -",
            size_hint=(1, None),
            height=dp(30),
            color=self.COLOR_TEXTO
        )

        self.input_precio_venta = TextInput(hint_text="Precio al que lo venderás", multiline=False, input_filter='float')

        self.btn_seleccionar_img = Button(
            text="Seleccionar imagen",
            size_hint=(1, None),
            height=dp(40),
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON
        )
        self.btn_seleccionar_img.bind(on_press=self.abrir_selector_imagen)

        self.img_ruta = None
        self.lbl_imagen = Label(
            text="No hay imagen seleccionada",
            size_hint=(1, None),
            height=dp(30),
            color=self.COLOR_TEXTO
        )

        self.form_layout.add_widget(self.input_nombre)
        self.form_layout.add_widget(self.input_costo)
        self.form_layout.add_widget(self.input_piezas)
        self.form_layout.add_widget(self.btn_calcular_sugerido)
        self.form_layout.add_widget(self.lbl_precio_sugerido)
        self.form_layout.add_widget(self.input_precio_venta)
        self.form_layout.add_widget(self.btn_seleccionar_img)
        self.form_layout.add_widget(self.lbl_imagen)

        self.btn_agregar = Button(
            text="Agregar producto",
            size_hint=(1, None),
            height=dp(50),
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON
        )
        self.btn_agregar.bind(on_press=self.agregar_producto)
        self.form_layout.add_widget(self.btn_agregar)
        
    def _update_form_rect(self, instance, value):
        self.form_rect.pos = instance.pos
        self.form_rect.size = instance.size

    def calcular_precio_sugerido(self, instance):
        try:
            costo_total = float(self.input_costo.text)
            piezas = int(self.input_piezas.text)
            if piezas <= 0 or costo_total <= 0:
                self.lbl_precio_sugerido.text = "Precio sugerido: Valores deben ser > 0"
                return
            costo_unitario = costo_total / piezas
            precio_sugerido = costo_unitario * 1.8
            self.lbl_precio_sugerido.text = f"Precio sugerido: ${precio_sugerido:.2f}"
        except ValueError:
            self.lbl_precio_sugerido.text = "Precio sugerido: Ingresa valores válidos"

    def toggle_formulario(self, instance):
        if not self.formulario_popup:
            self.formulario_popup = Popup(title="Agregar Producto", content=self.form_layout, size_hint=(0.9, 0.8))
        self.formulario_popup.open()

    def abrir_selector_imagen(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=10)
        filechooser = FileChooserIconView(
            path=str(Path.home() / "Downloads"),
            filters=['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp'],
            size_hint=(1, 0.9)
        )

        btn_seleccionar = Button(
            text="Seleccionar Imagen",
            size_hint=(1, 0.1),
            background_color=self.COLOR_BOTON,
            color=self.COLOR_TEXTO_BOTON
        )
        layout.add_widget(filechooser)
        layout.add_widget(btn_seleccionar)

        popup = Popup(title="Selecciona una imagen", content=layout, size_hint=(0.9, 0.9))

        def seleccionar_foto(instance_sel):
            selection = filechooser.selection
            if selection:
                self.img_ruta = selection[0]
                self.lbl_imagen.text = f"Imagen: {os.path.basename(self.img_ruta)}"
                popup.dismiss()

        btn_seleccionar.bind(on_press=seleccionar_foto)
        popup.open()

    def agregar_producto(self, instance):
        try:
            nombre = self.input_nombre.text.strip()
            costo_total = float(self.input_costo.text)
            piezas = int(self.input_piezas.text)
            precio_venta = float(self.input_precio_venta.text)

            if piezas <= 0 or costo_total <= 0 or precio_venta <= 0:
                self.mostrar_error("Los valores numéricos deben ser mayores a cero.")
                return
            if not nombre:
                self.mostrar_error("Debe ingresar el nombre del producto.")
                return

            costo_unitario = costo_total / piezas
            precio_sugerido = costo_unitario * 1.8

            producto = {
                "nombre": nombre,
                "costo_unitario": costo_unitario,
                "precio_sugerido": precio_sugerido,
                "precio_final": precio_venta,
                "piezas": piezas,
                "imagen": self.img_ruta
            }

            self.inventario.append(producto)
            self.guardar_inventario()
            self.limpiar_formulario()
            if self.formulario_popup:
                self.formulario_popup.dismiss()
            self.mostrar_inventario()

        except ValueError:
            self.mostrar_error("Por favor, ingresa valores numéricos válidos.")

    def limpiar_formulario(self):
        self.input_nombre.text = ""
        self.input_costo.text = ""
        self.input_piezas.text = ""
        self.input_precio_venta.text = ""
        self.img_ruta = None
        self.lbl_imagen.text = "No hay imagen seleccionada"
        self.lbl_precio_sugerido.text = "Precio sugerido: -"

    def mostrar_error(self, mensaje):
        popup = Popup(
            title="Error",
            content=Label(text=mensaje, color=self.COLOR_ERROR),
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def mostrar_inventario(self):
        self.inventario_list.clear_widgets()
        for idx, prod in enumerate(self.inventario):
            tarjeta = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(120), padding=dp(5), spacing=dp(10))
            
            if prod["imagen"]:
                img = Image(source=prod["imagen"], size_hint=(None, None), size=(dp(100), dp(100)), allow_stretch=True)
            else:
                img = Label(text="Sin imagen", size_hint=(None, None), size=(dp(100), dp(100)), halign='center', valign='middle', color=self.COLOR_TEXTO)

            tarjeta.add_widget(img)

            datos = BoxLayout(orientation='vertical')
            lbl_nombre = ProductoLabel(text=prod["nombre"], font_size=18, bold=True, index=idx, color=self.COLOR_TEXTO)
            lbl_nombre.bind(on_touch_down=self.seleccionar_producto)
            datos.add_widget(lbl_nombre)

            datos.add_widget(Label(text=f"Costo unitario: ${prod['costo_unitario']:.2f}", color=self.COLOR_TEXTO))
            datos.add_widget(Label(text=f"Precio sugerido: ${prod['precio_sugerido']:.2f}", color=self.COLOR_TEXTO))
            datos.add_widget(Label(text=f"Precio final: ${prod['precio_final']:.2f}", color=self.COLOR_TEXTO))
            datos.add_widget(Label(text=f"Piezas: {prod['piezas']}", color=self.COLOR_TEXTO))

            tarjeta.add_widget(datos)

            self.inventario_list.add_widget(tarjeta)

        self.producto_seleccionado = None
        self.btn_eliminar.disabled = True
 
    def seleccionar_producto(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.producto_seleccionado = instance.index
            self.btn_eliminar.disabled = False
            self.btn_editar.disabled = False
    def editar_producto(self, instance):
        if self.producto_seleccionado is not None:
            producto = self.inventario[self.producto_seleccionado]
            self.input_nombre.text = producto['nombre']
            self.input_costo.text = str(producto['costo_unitario'] * producto['piezas'])
            self.input_piezas.text = str(producto['piezas'])
            self.input_precio_venta.text = str(producto['precio_final'])
            self.img_ruta = producto['imagen']
            self.lbl_imagen.text = f"Imagen: {os.path.basename(self.img_ruta)}" if self.img_ruta else "No hay imagen seleccionada"
        # Reabrir el popup
            if not self.formulario_popup:
                self.formulario_popup = Popup(title="Editar Producto", content=self.form_layout, size_hint=(0.9, 0.8))
        else:
            self.formulario_popup.title = "Editar Producto"
        # Cambiar texto del botón agregar
        self.btn_agregar.text = "Guardar cambios"
        self.btn_agregar.unbind(on_press=self.agregar_producto)
        self.btn_agregar.bind(on_press=self.guardar_edicion_producto)
        self.formulario_popup.open()
    def guardar_edicion_producto(self, instance):
        try:
            nombre = self.input_nombre.text.strip()
            costo_total = float(self.input_costo.text)
            piezas = int(self.input_piezas.text)
            precio_venta = float(self.input_precio_venta.text)
            if piezas <= 0 or costo_total <= 0 or precio_venta <= 0 or not nombre:
                self.mostrar_error("Revisa que todos los campos tengan valores válidos.")
                return
            costo_unitario = costo_total / piezas
            precio_sugerido = costo_unitario * 1.8
            producto = self.inventario[self.producto_seleccionado]
            producto.update({
                "nombre": nombre,
                "costo_unitario": costo_unitario,
                "precio_sugerido": precio_sugerido,
                "precio_final": precio_venta,
                "piezas": piezas,
                "imagen": self.img_ruta
                })
            self.guardar_inventario()
            self.mostrar_inventario()
            self.formulario_popup.dismiss()
            self.limpiar_formulario()
            self.btn_agregar.text = "Agregar producto"
            self.btn_agregar.unbind(on_press=self.guardar_edicion_producto)
            self.btn_agregar.bind(on_press=self.agregar_producto)
        except ValueError:
            self.mostrar_error("Por favor, ingresa valores numéricos válidos.") 
    def eliminar_producto(self, instance):
        if self.producto_seleccionado is not None:
            self.inventario.pop(self.producto_seleccionado)
            self.guardar_inventario()
            self.mostrar_inventario()

    def guardar_inventario(self):
        print("Cargando inventario:")
        for i, item in enumerate(self.inventario):
            print(f"{i}: {item}")
        
        try:
            with open(self.ARCHIVO_INVENTARIO, "w", encoding="utf-8") as f:
                json.dump(self.inventario, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.mostrar_error(f"No se pudo guardar inventario: {e}")

    def cargar_inventario(self):
        if os.path.exists(self.ARCHIVO_INVENTARIO):
            try:
                with open(self.ARCHIVO_INVENTARIO, "r", encoding="utf-8") as f:
                    self.inventario = json.load(f)
            except Exception as e:
                self.mostrar_error(f"No se pudo cargar inventario: {e}")
                self.inventario = []
    def registrar_venta(self, total, detalles):
        venta = {"fecha": datetime.now().isoformat(), "monto": total, "detalles": detalles}
        self.historial_ventas.append(venta)
        try:
            with open(self.ARCHIVO_VENTAS, "w", encoding="utf-8") as f:
                json.dump(self.historial_ventas, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.mostrar_error(f"No se pudo guardar la venta: {e}")
    def cargar_ventas(self):
        if os.path.exists(self.ARCHIVO_VENTAS):
            try:
                with open(self.ARCHIVO_VENTAS, "r", encoding="utf-8") as f:
                    self.historial_ventas = json.load(f)
            except Exception as e:
                    self.mostrar_error(f"No se pudieron cargar las ventas: {e}")
                    self.historial_ventas = []
        else:
            # Aquí garantizamos que esté inicializado
            self.historial_ventas = []
    def calcular_corte_por_dia(self, fecha_str):
        ventas_dia = [v for v in self.historial_ventas if v['fecha'].startswith(fecha_str)]
        total = sum(v['monto'] for v in ventas_dia)
        self.lbl_corte_resultado.text = f"Corte del {fecha_str}:\nTotal: ${total:.2f}"
        
    def calcular_corte_diario_por_input(self, instance):
        fecha_str = self.selector_fecha.text.strip()
        if not fecha_str:
            self.lbl_corte_resultado.text = "Ingresa una fecha válida"
            return
        self.calcular_corte_por_dia(fecha_str)
    
    def ver_corte_semanal(self, instance):
        hoy = datetime.now()
        hace_7_dias = hoy - timedelta(days=7)
        total = sum(v["monto"] for v in self.historial_ventas if datetime.fromisoformat(v["fecha"]) >= hace_7_dias)
        self.lbl_corte_resultado.text = f"Corte de los últimos 7 días:\nTotal: ${total:.2f}"
    def ver_corte_mensual(self, instance):
        hoy = datetime.now()
        hace_30_dias = hoy - timedelta(days=30)
        total = sum(v["monto"] for v in self.historial_ventas if datetime.fromisoformat(v["fecha"]) >= hace_30_dias)
        self.lbl_corte_resultado.text = f"Corte de los últimos 30 días:\nTotal: ${total:.2f}"
    def ver_estadisticas(self, instance):
        hoy = datetime.now()
        hace_7_dias = hoy - timedelta(days=7)
        hace_30_dias = hoy - timedelta(days=30)
        contador_semanal = {}
        contador_mensual = {}
        for venta in self.historial_ventas:
            fecha = datetime.fromisoformat(venta["fecha"])
            if "detalles" in venta:  # Asegúrate de guardar esto en el futuro
                if fecha >= hace_7_dias:
                    for nombre in venta['detalles']:
                        contador_semanal[nombre] = contador_semanal.get(nombre, 0) + 1
                       
                    if fecha >= hace_30_dias:
                        for nombre in venta['detalles']:
                            contador_mensual[nombre] = contador_mensual.get(nombre, 0) + 1
        def obtener_top(diccionario):
            if diccionario:
                return max(diccionario, key=diccionario.get)
            return "Ninguno"
        top_semana = obtener_top(contador_semanal)
        top_mes = obtener_top(contador_mensual)
        self.lbl_corte_resultado.text = (
            f"Producto más vendido en la semana: {top_semana}\n"
            f"Producto más vendido en el mes: {top_mes}"
        )
    def obtener_top_productos(self, n=10):
        if not hasattr(self, 'historial_ventas') or not self.historial_ventas:
            return []  # <- Asegúrate de que devuelva una lista vacía si no hay ventas
        contador = Counter()
        for venta in self.historial_ventas:
            productos = venta.get("detalles", [])
            contador.update(productos)
        return [nombre for nombre, _ in contador.most_common(n)]
         
class PantallaVenta(Screen):
    COLOR_FONDO = get_color_from_hex("#DCF6F9")
    COLOR_BOTON = get_color_from_hex("#94296E")
    COLOR_TEXTO_BOTON = get_color_from_hex("#F8F8F8CD")
    COLOR_TEXTO = get_color_from_hex("#9B0857")
    COLOR_ERROR = get_color_from_hex("#B8454F")
    COLOR_BOTONRapido = get_color_from_hex("#6A1ED5")
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        #self.carrito = [] 
        self.app = app
        self.venta_actual = []
        self.total = 0.0
        
        #self._actualizar_carrito = [] 
        # Scroll para todo el contenido
        contenedor_scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None
        )
        layout.bind(minimum_height=layout.setter('height'))  # Ajusta la altura al contenido

        with layout.canvas.before:
            Color(*get_color_from_hex("#FFF0F5"))
            self.fondo_rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._actualizar_fondo_rect, pos=self._actualizar_fondo_rect)
        
         # Buscar producto
        self.input_buscar = TextInput(hint_text="Buscar producto por nombre", multiline=False,size_hint_y=None,height=dp(30) )
        self.input_buscar.unbind(text=self.actualizar_resultados_busqueda)
        layout.add_widget(self.input_buscar)
        
        self.botones_rapidos = GridLayout(cols=2, size_hint_y=None, height=dp(5*30 + 4*5), spacing=dp(2))
        self.botones_rapidos.bind(minimum_height=self.botones_rapidos.setter('height'))
        self.botones_rapidos.height = dp(5*30 + 4*5)

        # Esto es 5 filas de 30dp + 4 espacios de 5dp = 150 + 20 = 170 dp altura total aprox
        layout.add_widget(self.botones_rapidos)
        self.actualizar_botones_rapidos()  # Llamamos a este método que vamos a crear
        
        
       

        # Resultados
        self.resultados_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.resultados_layout.bind(minimum_height=self.resultados_layout.setter('height'))

        self.scroll_resultados = ScrollView(size_hint=(1, None), height=dp(80))
        self.scroll_resultados.add_widget(self.resultados_layout)
        layout.add_widget(self.scroll_resultados)

        # Lista de compra
        self.carrito_label = Label(text="Carrito vacío", size_hint=(1, None), height=dp(100), color='black')
        layout.add_widget(self.carrito_label)

        # Total
        self.lbl_total = Label(text="Total: $0.00", size_hint=(1, None), height=dp(50),color='black')
        layout.add_widget(self.lbl_total)

        # Pago
        self.input_pago = TextInput(hint_text="Pago recibido", input_filter='float', multiline=False, size_hint_y=None,height=dp(40))
        layout.add_widget(self.input_pago)

        # Cambio
        self.lbl_cambio = Label(text="Cambio: $0.00", size_hint=(1, None), height=dp(30),color='black')
        layout.add_widget(self.lbl_cambio)
        # Botón cobrar
        btn_cobrar = Button(
            text="Cobrar",
            size_hint=(1, None),
            height=dp(50),
            background_color=app.COLOR_BOTON,
            color=app.COLOR_TEXTO_BOTON,
            on_press=self.calcular_cambio
        )
        layout.add_widget(btn_cobrar)
        # Botón confirmar venta
        btn_confirmar = Button(
            text="Confirmar venta",
            size_hint=(1, None),
            height=dp(50),
            background_color=app.COLOR_BOTON,
            color=app.COLOR_TEXTO_BOTON,
            on_press=self.confirmar_venta
        )
        layout.add_widget(btn_confirmar)
        # Botón para volver al menú
        btn_volver2 = Button(text="Volver al menú", size_hint=(1, None), height=dp(40), background_color=app.COLOR_BOTON,  color=app.COLOR_TEXTO_BOTON, on_press=lambda x: setattr (self.app.sm,'current',  'menu'))
        layout.add_widget(btn_volver2)


        contenedor_scroll.add_widget(layout)
        self.add_widget(contenedor_scroll)
    def on_pre_enter(self):
        self.resultados_layout.clear_widgets()
    
        # Desvincula temporalmente el evento para evitar que se dispare innecesariamente
        self.input_buscar.unbind(text=self.actualizar_resultados_busqueda)
        self.input_buscar.text = ""
        self.input_buscar.bind(text=self.actualizar_resultados_busqueda)

        self.actualizar_botones_rapidos()
        
        
    
    def _actualizar_fondo_rect(self, instance, value):
        self.fondo_rect.pos = instance.pos
        self.fondo_rect.size = instance.size

    def volver_al_menu(self, instance):
        self.app.sm.current = 'menu'
    def actualizar_resultados_busqueda(self, instance, texto):
        try:
            texto = texto.lower().strip()
            self.resultados_layout.clear_widgets()
            if texto:  # Solo buscar si hay texto
                for producto in self.app.inventario:
                    if texto in producto['nombre'].lower():
                        btn = Button(
                            text=f"{producto['nombre']} - ${producto['precio_final']:.2f}",
                            size_hint_y=None,
                            height=dp(40),
                            background_normal='',       # ← Quita la imagen de fondo
                            background_color=PantallaVenta.COLOR_BOTON,
                            color=PantallaVenta.COLOR_TEXTO_BOTON,
                            on_press=lambda btn, p=producto: self.agregar_al_carrito(p)
                        )
                        self.resultados_layout.add_widget(btn)
            else:
                # Si no hay texto, muestra los botones rápidos actualizados
                self.actualizar_botones_rapidos()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.lbl_cambio.text = f"Error en búsqueda: {str(e)}"


    def agregar_al_carrito(self, producto):
        if producto['piezas'] <= 0:
            self.lbl_cambio.text = f"No hay existencias de '{producto['nombre']}'" 
            return
        self.venta_actual.append(producto)
        self.total += producto['precio_final']
        self.carrito_label.text = '\n'.join([f"{p['nombre']} - ${p['precio_final']:.2f}" for p in self.venta_actual])
        self.lbl_total.text = f"Total: ${self.total:.2f}"
        
    def actualizar_botones_rapidos(self): 
        print(f"Inventario actual: {self.app.inventario}")

        self.botones_rapidos.clear_widgets()
        top_nombres = self.app.obtener_top_productos(10) or []  # ← Esto evita que 'None' cause error
        #top_nombres = [p['nombre'] for p in self.app.inventario[:10]]

        print(f"Top productos: {top_nombres}")  # ← ¡Esto nos dirá si hay datos!

        for nombre in top_nombres:
            producto = next((p for p in self.app.inventario if p['nombre'] == nombre), None)
            if producto:
                btn = Button(
                    text=producto['nombre'],
                    size_hint=(0.48, None),  # Fijo ancho y alto
                    size=(dp(140), dp(30)),  # 140 dp ancho y 30 dp alto (ajustable)
                    background_normal='',       # ← Quita la imagen de fondo
                    background_color=PantallaVenta.COLOR_BOTONRapido, 
                    color=PantallaVenta.COLOR_TEXTO_BOTON,
                    #on_press=lambda btn, p=producto: self.agregar_al_carrito(p)
                )
                btn.bind(on_press=lambda btn, p=producto: self.agregar_al_carrito(p))
                self.botones_rapidos.add_widget(btn)  
    def calcular_cambio(self, instance):
        try:
            texto_pago = self.input_pago.text.strip()
            if not texto_pago.replace('.', '', 1).isdigit():
                self.lbl_cambio.text = "Ingresa un número válido"
                return
            pago = float(texto_pago)
            if pago < self.total:
                self.lbl_cambio.text = "Pago insuficiente"
                return
            cambio = pago - self.total
            self.lbl_cambio.text = f"Cambio: ${cambio:.2f}"
        except Exception as e:
            self.lbl_cambio.text = f"Error: {str(e)}"

    def confirmar_venta(self, instance):
        

        try:
            texto_pago = self.input_pago.text.strip()
            if not texto_pago:
                self.lbl_cambio.text = "Por favor ingresa el monto de pago"
                return

            try:
                pago = float(texto_pago)
            except ValueError:
                self.lbl_cambio.text = "Ingresa un número válido"
                return
            if pago < self.total:
                self.lbl_cambio.text = "Pago insuficiente"
                return

            cambio = pago - self.total
            self.lbl_cambio.text = f"Cambio: ${cambio:.2f}"

            # Descontar del inventario
            for p in self.venta_actual:
                for inv in self.app.inventario:
                    if p['nombre'] == inv['nombre'] and inv['piezas'] > 0:
                        inv['piezas'] -= 1

            # Guardar venta
            nombres_productos = [p['nombre'] for p in self.venta_actual]
            self.app.registrar_venta(self.total, nombres_productos)
            self.app.guardar_inventario()
            self.app.mostrar_inventario()
            self.actualizar_botones_rapidos()
            # Limpiar datos de venta
            self.venta_actual.clear()
            self.total = 0
            self.carrito_label.text = "Carrito vacío"
            self.lbl_total.text = "Total: $0.00"
            self.input_pago.text = ""
            self.lbl_cambio.text = "Cambio: $0.00"

            # Regresar al menú principal
            self.app.sm.current = 'menu'

        except Exception as e:
            self.lbl_cambio.text = f"Error: {str(e)}"
    
        
if __name__ == '__main__':
    try:
        InventarioApp().run()
    except Exception as e:
        import traceback
        with open("/sdcard/error_log.txt", "w", encoding="utf-8") as f:
            f.write("ERROR al iniciar la app:")
            f.write(str(e) + "")
            traceback.print_exc(file=f)
