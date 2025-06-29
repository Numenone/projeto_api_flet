import flet as ft
import requests
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
import base64
import asyncio

# Configurar o backend do Matplotlib para não usar GUI
matplotlib.use('Agg')

# Configurações da API
API_URL = "http://localhost:3000"
PRODUCTS_ENDPOINT = f"{API_URL}/products"
CATEGORIES_ENDPOINT = f"{API_URL}/categories"

class ProductApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.products = []
        self.categories = []
        self.setup_ui()  # Primeiro cria a UI
        self.load_data()  # Depois carrega os dados
    
    def setup_page(self):
        self.page.title = "Sistema de Gerenciamento de Produtos"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width = 1000
        self.page.window_height = 700
    
    def load_data(self):
        try:
        # Carrega produtos e categorias
            products_response = requests.get(PRODUCTS_ENDPOINT)
            categories_response = requests.get(CATEGORIES_ENDPOINT)
        
            if products_response.status_code == 200:
                self.products = products_response.json()
            else:
                self.products = []
                print(f"Erro ao carregar produtos: {products_response.status_code}")
        
            if categories_response.status_code == 200:
                self.categories = categories_response.json()
                # Atualiza ambos dropdowns quando os dados são carregados
                self.update_search_category_dropdown()
            else:
                self.categories = []
                print(f"Erro ao carregar categorias: {categories_response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
            self.products = []
            self.categories = []
            self.show_snackbar("Erro ao conectar com o servidor!")
    
    def setup_ui(self):
        self.current_tab_index = 0
        self.tab_contents = [
            self.create_registration_tab(),
            self.create_charts_tab(),
            self.create_search_tab()
        ]
        
        self.tab_buttons = ft.Row(
            controls=[
                ft.ElevatedButton("Cadastro", on_click=lambda e: self.switch_tab(0)),
                ft.ElevatedButton("Gráficos", on_click=lambda e: self.switch_tab(1)),
                ft.ElevatedButton("Pesquisa", on_click=lambda e: self.switch_tab(2))
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        self.content_area = ft.Column(
            controls=[self.tab_contents[self.current_tab_index]],
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
        
        self.page.add(
            ft.Column(
                controls=[
                    self.tab_buttons,
                    ft.Divider(height=1),
                    self.content_area
                ],
                expand=True
            )
        )

        self.update_category_dropdown()
        if hasattr(self, 'search_category'):
            self.update_search_category_dropdown()
    
    def update_search_category_dropdown(self):
        if hasattr(self, 'search_category'):
            self.search_category.options = [ft.dropdown.Option("Todas")] + [
                ft.dropdown.Option(cat["name"]) for cat in self.categories
            ]
            self.page.update()

    def switch_tab(self, tab_index):
        self.current_tab_index = tab_index
        self.content_area.controls[0] = self.tab_contents[tab_index]
    
        # Se for a aba de pesquisa, atualiza o dropdown de categorias
        if tab_index == 2:  # Índice da aba de pesquisa
            self.update_search_category_dropdown()
        
        self.page.update()
    
    def create_registration_tab(self):
        # Campos do formulário
        self.name_field = ft.TextField(
            label="Nome do Produto", 
            width=400,
            autofocus=True
        )
        self.price_field = ft.TextField(
            label="Preço", 
            width=200, 
            input_filter=ft.NumbersOnlyInputFilter(),
            prefix_text="R$ "
        )
        self.quantity_field = ft.TextField(
            label="Quantidade", 
            width=150, 
            input_filter=ft.NumbersOnlyInputFilter()
        )
        
        # Campo para nova categoria
        self.new_category_field = ft.TextField(
            label="Nova Categoria", 
            width=300, 
            visible=False
        )
        
        # Dropdown de categorias
        self.category_dropdown = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[ft.dropdown.Option("Selecione uma categoria")],
        )
        
        # Botões
        self.toggle_category_button = ft.ElevatedButton(
            "Nova Categoria",
            icon="ADD",
            on_click=self.toggle_new_category_field
        )
        
        self.save_category_button = ft.ElevatedButton(
            "Salvar Categoria",
            icon="SAVE",
            on_click=self.save_category,
            visible=False
        )
        
        self.save_button = ft.ElevatedButton(
            text="Salvar",
            icon="SAVE",
            on_click=self.save_product,
        )
        
        # Lista de produtos
        self.products_list = ft.ListView(expand=True)
        
        # Atualiza os controles
        self.update_category_dropdown()
        self.update_products_list()
        
        return ft.Column(
            controls=[
                ft.Text("Cadastro de Produtos", size=24, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Row([self.name_field, self.price_field, self.quantity_field]),
                    ft.Row([self.category_dropdown, self.toggle_category_button]),
                    ft.Row([self.new_category_field, self.save_category_button]),
                    ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END)
                ]),
                ft.Divider(height=1),
                ft.Text("Lista de Produtos", size=20, weight=ft.FontWeight.BOLD),
                self.products_list,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def toggle_new_category_field(self, e):
        self.new_category_field.visible = not self.new_category_field.visible
        self.save_category_button.visible = self.new_category_field.visible
        self.category_dropdown.visible = not self.new_category_field.visible
        self.page.update()
    
    def save_category(self, e):
        category_name = self.new_category_field.value.strip()
    
        if not category_name:
            self.show_snackbar("Nome da categoria é obrigatório!")
            return
        
        if any(cat["name"].lower() == category_name.lower() for cat in self.categories):
            self.show_snackbar("Esta categoria já existe!")
            return
        
        try:
            response = requests.post(
                CATEGORIES_ENDPOINT, 
                json={"name": category_name}
            )
        
            if response.status_code == 201:
                new_category = response.json()
                self.categories.append(new_category)
                self.show_snackbar("Categoria cadastrada com sucesso!")
                self.update_category_dropdown()
                self.update_search_category_dropdown()
                self.new_category_field.value = ""
                self.toggle_new_category_field(None)
                self.load_data()  # Recarrega os dados para garantir sincronização
            else:
                self.show_snackbar(f"Erro ao cadastrar categoria: {response.text}")
            
        except requests.exceptions.RequestException:
            self.show_snackbar("Erro de conexão com a API!")
    
    def update_category_dropdown(self):
        options = [ft.dropdown.Option("Selecione uma categoria")]
        options.extend(ft.dropdown.Option(cat["name"]) for cat in self.categories)
        self.category_dropdown.options = options
        self.page.update()
    
    def update_products_list(self):
        self.products_list.controls.clear()
        
        if not self.products:
            self.products_list.controls.append(
                ft.ListTile(title=ft.Text("Nenhum produto cadastrado.")))
            self.page.update()
            return
            
        for product in sorted(self.products, key=lambda x: x['name']):
            category_name = next(
                (cat["name"] for cat in self.categories if cat["id"] == product.get("categoryId")), 
                "Sem categoria"
            )
            
            created_at = datetime.fromisoformat(product["createdAt"]).strftime("%d/%m/%Y %H:%M") 
            
            product_item = ft.ListTile(
                title=ft.Text(product["name"]),
                subtitle=ft.Text(
                    f"Preço: R${product['price']:.2f} | "
                    f"Quantidade: {product['quantity']} | "
                    f"Categoria: {category_name}\n"
                    f"Cadastrado em: {created_at}"
                ),
                trailing=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon="EDIT",
                            tooltip="Editar",
                            on_click=lambda e, p=product: self.edit_product(p),
                        ),
                        ft.IconButton(
                            icon="DELETE",
                            tooltip="Excluir",
                            on_click=lambda e, p=product: self.delete_product(p),
                            icon_color="red"
                        ),
                    ],
                    width=100,
                ),
            )
            self.products_list.controls.append(product_item)
        
        self.page.update()
    
    def save_product(self, e):
        # Validação dos campos
        name = self.name_field.value.strip()
        price = self.price_field.value.strip()
        quantity = self.quantity_field.value.strip()
        
        if not name:
            self.show_snackbar("Nome do produto é obrigatório!")
            return
        
        try:
            price = float(price) if price else 0.0
            quantity = int(quantity) if quantity else 0
        except ValueError:
            self.show_snackbar("Preço e quantidade devem ser números válidos!")
            return
        
        # Obtém a categoria selecionada
        category_name = self.category_dropdown.value
        if not category_name or category_name == "Selecione uma categoria":
            self.show_snackbar("Selecione uma categoria!")
            return
            
        category_id = next(
            (cat["id"] for cat in self.categories if cat["name"] == category_name), 
            None
        )
        
        # Prepara o novo produto
        new_product = {
            "name": name,
            "price": price,
            "quantity": quantity,
            "categoryId": category_id,
            "createdAt": datetime.now().isoformat(),
        }
        
        try:
            if hasattr(self, 'editing_product_id'):
                # Atualização de produto existente
                response = requests.put(
                    f"{PRODUCTS_ENDPOINT}/{self.editing_product_id}", 
                    json=new_product
                )
                if response.status_code == 200:
                    self.show_snackbar("Produto atualizado com sucesso!")
                    del self.editing_product_id
                else:
                    self.show_snackbar(f"Erro ao atualizar produto: {response.text}")
            else:
                # Cadastro de novo produto
                response = requests.post(PRODUCTS_ENDPOINT, json=new_product)
                if response.status_code == 201:
                    self.show_snackbar("Produto cadastrado com sucesso!")
            
            self.load_data()
            self.clear_form()
            self.update_products_list()
            
        except requests.exceptions.RequestException:
            self.show_snackbar("Erro de conexão com a API!")
    
    def edit_product(self, product):
        self.name_field.value = product["name"]
        self.price_field.value = str(product["price"])
        self.quantity_field.value = str(product["quantity"])
        
        category_name = next(
            (cat["name"] for cat in self.categories if cat["id"] == product.get("categoryId")), 
            ""
        )
        self.category_dropdown.value = category_name
        
        self.save_button.text = "Atualizar"
        self.editing_product_id = product["id"]
        self.page.update()
    
    def delete_product(self, product):
        try:
            response = requests.delete(f"{PRODUCTS_ENDPOINT}/{product['id']}")
            if response.status_code == 200:
                self.show_snackbar("Produto excluído com sucesso!")
                self.products = [p for p in self.products if p['id'] != product['id']]
                self.update_products_list()
            else:
                self.show_snackbar(f"Erro ao excluir produto: {response.text}")
        except requests.exceptions.RequestException as e:
            self.show_snackbar(f"Erro de conexão: {str(e)}")
    
    def create_charts_tab(self):
        self.chart_type_dropdown = ft.Dropdown(
            label="Tipo de Gráfico",
            options=[
                ft.dropdown.Option("Quantidade por Categoria"),
                ft.dropdown.Option("Preço Médio por Categoria"),
                ft.dropdown.Option("Distribuição de Preços"),
            ],
            value="Quantidade por Categoria",
            width=300
        )
        
        self.generate_button = ft.ElevatedButton(
            "Gerar Gráfico",
            icon="INSERT_CHART",
            on_click=self.generate_chart
        )
        
        self.chart_image = ft.Image(
            width=800, 
            height=400,
            fit=ft.ImageFit.CONTAIN
        )
        
        return ft.Column(
            controls=[
                ft.Text("Gráficos de Produtos", size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [self.chart_type_dropdown, self.generate_button],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(height=1),
                ft.Container(
                    content=self.chart_image,
                    alignment=ft.alignment.center,
                    padding=10
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    def generate_chart(self, e):
        chart_type = self.chart_type_dropdown.value
        
        if chart_type == "Quantidade por Categoria":
            self.generate_quantity_by_category_chart()
        elif chart_type == "Preço Médio por Categoria":
            self.generate_avg_price_by_category_chart()
        elif chart_type == "Distribuição de Preços":
            self.generate_price_distribution_chart()
    
    def generate_quantity_by_category_chart(self):
        category_quantities = {}
        
        for product in self.products:
            category_name = next(
                (cat["name"] for cat in self.categories if cat["id"] == product.get("categoryId")), 
                "Sem categoria"
            )
            
            if category_name not in category_quantities:
                category_quantities[category_name] = 0
            category_quantities[category_name] += product["quantity"]
        
        # Ordena por quantidade
        sorted_categories = sorted(category_quantities.items(), key=lambda x: x[1], reverse=True)
        categories = [x[0] for x in sorted_categories]
        quantities = [x[1] for x in sorted_categories]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(categories, quantities, color='skyblue')
        
        # Adiciona os valores nas barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, 
                    f'{int(width)}', 
                    va='center', ha='left')
        
        ax.set_title("Quantidade de Produtos por Categoria", pad=20)
        ax.set_xlabel("Quantidade Total")
        ax.set_ylabel("Categoria")
        plt.tight_layout()
        
        self.display_chart(fig)
    
    def generate_avg_price_by_category_chart(self):
        category_prices = {}
        
        for product in self.products:
            category_name = next(
                (cat["name"] for cat in self.categories if cat["id"] == product.get("categoryId")), 
                "Sem categoria"
            )
            
            if category_name not in category_prices:
                category_prices[category_name] = []
            category_prices[category_name].append(product["price"])
        
        # Calcula a média e ordena
        category_avg = {k: sum(v)/len(v) for k, v in category_prices.items()}
        sorted_categories = sorted(category_avg.items(), key=lambda x: x[1], reverse=True)
        categories = [x[0] for x in sorted_categories]
        averages = [x[1] for x in sorted_categories]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(categories, averages, color='lightgreen')
        
        # Adiciona os valores nas barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, 
                    f'R${width:.2f}', 
                    va='center', ha='left')
        
        ax.set_title("Preço Médio por Categoria", pad=20)
        ax.set_xlabel("Preço Médio (R$)")
        ax.set_ylabel("Categoria")
        plt.tight_layout()
        
        self.display_chart(fig)
    
    def generate_price_distribution_chart(self):
        prices = [p["price"] for p in self.products]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(prices, bins=10, color='orange', edgecolor='black')
        
        ax.set_title("Distribuição de Preços dos Produtos", pad=20)
        ax.set_xlabel("Preço (R$)")
        ax.set_ylabel("Quantidade de Produtos")
        plt.tight_layout()
        
        self.display_chart(fig)
    
    def display_chart(self, fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=100)
        buf.seek(0)
        self.chart_image.src_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        self.page.update()
    
    def create_search_tab(self):
        self.search_name = ft.TextField(
            label="Nome do Produto", 
            width=300,
            hint_text="Digite parte do nome"
        )
    
        self.search_category = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[ft.dropdown.Option("Todas")] + [
                ft.dropdown.Option(cat["name"]) for cat in self.categories
            ],
            value="Todas"
        )
        
        self.search_price_min = ft.TextField(
            label="Preço Mínimo", 
            width=150,
            input_filter=ft.NumbersOnlyInputFilter(),
            prefix_text="R$ "
        )
        
        self.search_price_max = ft.TextField(
            label="Preço Máximo", 
            width=150,
            input_filter=ft.NumbersOnlyInputFilter(),
            prefix_text="R$ "
        )
        
        self.search_button = ft.ElevatedButton(
            "Pesquisar",
            icon="SEARCH",
            on_click=self.search_products
        )
        
        self.clear_search_button = ft.ElevatedButton(
            "Limpar",
            icon="CLEAR",
            on_click=self.clear_search,
            color="red"
        )
        
        self.search_results = ft.ListView(
            expand=True,
            spacing=10,
            padding=10
        )
        
        return ft.Column(
            controls=[
                ft.Text("Pesquisa Avançada", size=24, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Row([self.search_name, self.search_category]),
                    ft.Row([self.search_price_min, self.search_price_max]),
                    ft.Row([
                        self.search_button,
                        self.clear_search_button
                    ], alignment=ft.MainAxisAlignment.END)
                ]),
                ft.Divider(height=1),
                self.search_results
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def search_products(self, e):
        name_filter = self.search_name.value.lower() if self.search_name.value else None
        category_filter = self.search_category.value if self.search_category.value != "Todas" else None
        
        try:
            price_min = float(self.search_price_min.value) if self.search_price_min.value else None
            price_max = float(self.search_price_max.value) if self.search_price_max.value else None
        except ValueError:
            self.show_snackbar("Preços devem ser números válidos!")
            return

        filtered_products = self.products
        
        if name_filter:
            filtered_products = [p for p in filtered_products if name_filter in p["name"].lower()]
        
        if category_filter:
            category_id = next(
                (cat["id"] for cat in self.categories if cat["name"] == category_filter), 
                None
            )
            if category_id:
                filtered_products = [p for p in filtered_products if p.get("categoryId") == category_id]
        
        if price_min is not None:
            filtered_products = [p for p in filtered_products if p["price"] >= price_min]
        
        if price_max is not None:
            filtered_products = [p for p in filtered_products if p["price"] <= price_max]
        
        self.search_results.controls.clear()
        
        if not filtered_products:
            self.search_results.controls.append(
                ft.ListTile(title=ft.Text("Nenhum produto encontrado.")))
        else:
            for product in filtered_products:
                category_name = next(
                    (cat["name"] for cat in self.categories if cat["id"] == product.get("categoryId")), 
                    "Sem categoria"
                )
                
                created_at = datetime.fromisoformat(product["createdAt"]).strftime("%d/%m/%Y %H:%M") 
                
                product_item = ft.ListTile(
                    title=ft.Text(product["name"]),
                    subtitle=ft.Text(
                        f"Preço: R${product['price']:.2f} | "
                        f"Quantidade: {product['quantity']} | "
                        f"Categoria: {category_name}\n"
                        f"Cadastrado em: {created_at}"
                    ),
                    on_click=lambda e, p=product: self.edit_product(p),
                )
                self.search_results.controls.append(product_item)
        
        self.page.update()
    
    def clear_search(self, e):
        self.search_name.value = ""
        self.search_category.value = "Todas"
        self.search_price_min.value = ""
        self.search_price_max.value = ""
        self.search_results.controls.clear()
        self.page.update()
    
    def clear_form(self):
        self.name_field.value = ""
        self.price_field.value = ""
        self.quantity_field.value = ""
        self.category_dropdown.value = "Selecione uma categoria"
        self.new_category_field.value = ""
        if hasattr(self, 'editing_product_id'):
            del self.editing_product_id
        self.save_button.text = "Salvar"
        self.page.update()
    
    def show_snackbar(self, message):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            action="OK",
            action_color="blue"
        )
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    # Configuração especial para Windows
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Cria e inicia a aplicação
    app = ProductApp(page)

if __name__ == "__main__":
    ft.app(target=main)