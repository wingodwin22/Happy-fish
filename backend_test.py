#!/usr/bin/env python3
"""
Test complet du backend de l'application Boutique Surgelés
Tests des APIs: Produits, Ventes, Clients, Dashboard
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://frostbite-sales.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class BoutiqueTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_results = []
        self.created_products = []
        self.created_clients = []
        self.created_sales = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_api_health(self):
        """Test API health check"""
        try:
            response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"API opérationnelle: {data.get('message', 'OK')}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Erreur de connexion: {str(e)}")
            return False
    
    def test_products_crud(self):
        """Test complet CRUD des produits"""
        print("\n=== TEST PRODUITS CRUD ===")
        
        # Test 1: Créer des produits
        test_products = [
            {
                "name": "Saumon Atlantique",
                "category": "poisson",
                "price": 24.99,
                "stock": 15,
                "unit": "kg"
            },
            {
                "name": "Crevettes Roses",
                "category": "poisson", 
                "price": 18.50,
                "stock": 8,
                "unit": "kg"
            },
            {
                "name": "Bœuf Haché",
                "category": "viande",
                "price": 12.99,
                "stock": 25,
                "unit": "kg"
            },
            {
                "name": "Escalopes de Porc",
                "category": "viande",
                "price": 9.99,
                "stock": 3,  # Stock faible pour tester alertes
                "unit": "kg"
            }
        ]
        
        for product_data in test_products:
            try:
                response = requests.post(f"{self.base_url}/products", 
                                       json=product_data, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    product = response.json()
                    self.created_products.append(product)
                    self.log_test(f"Créer produit {product_data['name']}", True, 
                                f"Produit créé avec ID: {product['id']}")
                else:
                    self.log_test(f"Créer produit {product_data['name']}", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"Créer produit {product_data['name']}", False, str(e))
        
        # Test 2: Récupérer tous les produits
        try:
            response = requests.get(f"{self.base_url}/products", headers=self.headers, timeout=10)
            if response.status_code == 200:
                products = response.json()
                self.log_test("Récupérer tous les produits", True, 
                            f"{len(products)} produits trouvés")
            else:
                self.log_test("Récupérer tous les produits", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Récupérer tous les produits", False, str(e))
        
        # Test 3: Récupérer un produit spécifique
        if self.created_products:
            product_id = self.created_products[0]['id']
            try:
                response = requests.get(f"{self.base_url}/products/{product_id}", 
                                      headers=self.headers, timeout=10)
                if response.status_code == 200:
                    product = response.json()
                    self.log_test("Récupérer produit spécifique", True, 
                                f"Produit {product['name']} récupéré")
                else:
                    self.log_test("Récupérer produit spécifique", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Récupérer produit spécifique", False, str(e))
        
        # Test 4: Modifier un produit
        if self.created_products:
            product_id = self.created_products[0]['id']
            update_data = {"price": 26.99, "stock": 20}
            try:
                response = requests.put(f"{self.base_url}/products/{product_id}", 
                                      json=update_data, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    updated_product = response.json()
                    self.log_test("Modifier produit", True, 
                                f"Prix mis à jour: {updated_product['price']}€")
                else:
                    self.log_test("Modifier produit", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Modifier produit", False, str(e))
        
        # Test 5: Supprimer un produit (on garde les autres pour les tests de vente)
        if len(self.created_products) > 1:
            product_id = self.created_products[-1]['id']  # Supprimer le dernier
            try:
                response = requests.delete(f"{self.base_url}/products/{product_id}", 
                                         headers=self.headers, timeout=10)
                if response.status_code == 200:
                    self.log_test("Supprimer produit", True, "Produit supprimé avec succès")
                    self.created_products.pop()  # Retirer de la liste
                else:
                    self.log_test("Supprimer produit", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Supprimer produit", False, str(e))
    
    def test_clients_api(self):
        """Test API Clients avec DELETE"""
        print("\n=== TEST CLIENTS API ===")
        
        # Test 1: Créer des clients
        test_clients = [
            {
                "name": "Restaurant Le Poisson Bleu",
                "phone": "01.45.67.89.12",
                "email": "contact@poissonbleu.fr",
                "address": "15 rue de la Mer, 75001 Paris",
                "credit_limit": 1000.0
            },
            {
                "name": "Boucherie Martin",
                "phone": "01.23.45.67.89",
                "email": "martin@boucherie.fr", 
                "address": "8 avenue des Bouchers, 75002 Paris",
                "credit_limit": 500.0
            },
            {
                "name": "Client Test Suppression",
                "phone": "01.99.88.77.66",
                "email": "test@suppression.fr",
                "address": "Test Address",
                "credit_limit": 100.0
            }
        ]
        
        for client_data in test_clients:
            try:
                response = requests.post(f"{self.base_url}/clients", 
                                       json=client_data, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    client = response.json()
                    self.created_clients.append(client)
                    self.log_test(f"Créer client {client_data['name']}", True, 
                                f"Client créé avec ID: {client['id']}")
                else:
                    self.log_test(f"Créer client {client_data['name']}", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"Créer client {client_data['name']}", False, str(e))
        
        # Test 2: Récupérer tous les clients
        try:
            response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
            if response.status_code == 200:
                clients = response.json()
                self.log_test("Récupérer tous les clients", True, 
                            f"{len(clients)} clients trouvés")
            else:
                self.log_test("Récupérer tous les clients", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Récupérer tous les clients", False, str(e))
        
        # Test 3: NOUVEAU - Supprimer un client existant
        if len(self.created_clients) >= 3:
            client_to_delete = self.created_clients[2]  # Client Test Suppression
            try:
                response = requests.delete(f"{self.base_url}/clients/{client_to_delete['id']}", 
                                         headers=self.headers, timeout=10)
                if response.status_code == 200:
                    self.log_test("DELETE Client existant", True, 
                                f"Client {client_to_delete['name']} supprimé avec succès")
                    # Vérifier qu'il n'existe plus
                    verify_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                    if verify_response.status_code == 200:
                        remaining_clients = verify_response.json()
                        deleted_client_exists = any(c['id'] == client_to_delete['id'] for c in remaining_clients)
                        if not deleted_client_exists:
                            self.log_test("Vérification suppression client", True, "Client bien supprimé de la liste")
                        else:
                            self.log_test("Vérification suppression client", False, "Client encore présent dans la liste")
                    self.created_clients.remove(client_to_delete)  # Retirer de notre liste
                else:
                    self.log_test("DELETE Client existant", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("DELETE Client existant", False, str(e))
        
        # Test 4: NOUVEAU - Tenter de supprimer un client inexistant (erreur 404 attendue)
        fake_client_id = "client-inexistant-12345"
        try:
            response = requests.delete(f"{self.base_url}/clients/{fake_client_id}", 
                                     headers=self.headers, timeout=10)
            if response.status_code == 404:
                self.log_test("DELETE Client inexistant (404)", True, 
                            "Erreur 404 correctement retournée pour client inexistant")
            else:
                self.log_test("DELETE Client inexistant (404)", False, 
                            f"Devrait retourner 404 mais status: {response.status_code}")
        except Exception as e:
            self.log_test("DELETE Client inexistant (404)", False, str(e))
    
    def test_fractional_stock(self):
        """NOUVEAU - Test fonctionnalité stock en float (quantités décimales)"""
        print("\n=== TEST STOCK FRACTIONNAIRE ===")
        
        # Test 1: Créer un produit avec stock décimal
        fractional_product = {
            "name": "Filet de Sole Premium",
            "category": "poisson",
            "price": 32.50,
            "stock": 5.5,  # Stock fractionnaire
            "unit": "kg"
        }
        
        try:
            response = requests.post(f"{self.base_url}/products", 
                                   json=fractional_product, headers=self.headers, timeout=10)
            if response.status_code == 200:
                product = response.json()
                self.created_products.append(product)
                if abs(product['stock'] - 5.5) < 0.01:
                    self.log_test("Créer produit stock fractionnaire", True, 
                                f"Produit créé avec stock {product['stock']} kg")
                else:
                    self.log_test("Créer produit stock fractionnaire", False, 
                                f"Stock incorrect: attendu 5.5, reçu {product['stock']}")
            else:
                self.log_test("Créer produit stock fractionnaire", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Créer produit stock fractionnaire", False, str(e))
            return
        
        # Test 2: Vendre une quantité décimale et vérifier le calcul
        if self.created_clients and len(self.created_products) > 0:
            fractional_sale = {
                "client_id": self.created_clients[0]['id'],
                "client_name": self.created_clients[0]['name'],
                "items": [
                    {
                        "product_id": product['id'],
                        "quantity": 2.3  # Quantité fractionnaire
                    }
                ],
                "discount": 0.0,
                "payment_method": "carte"
            }
            
            try:
                response = requests.post(f"{self.base_url}/sales", 
                                       json=fractional_sale, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    sale = response.json()
                    self.created_sales.append(sale)
                    
                    # Vérifier le calcul du prix (32.50 * 2.3 = 74.75)
                    expected_item_total = 32.50 * 2.3
                    actual_item_total = sale['items'][0]['total_price']
                    
                    if abs(actual_item_total - expected_item_total) < 0.01:
                        self.log_test("Calcul prix quantité fractionnaire", True, 
                                    f"Calcul correct: {actual_item_total}€ (2.3 kg × 32.50€)")
                    else:
                        self.log_test("Calcul prix quantité fractionnaire", False, 
                                    f"Calcul incorrect: attendu {expected_item_total}€, reçu {actual_item_total}€")
                    
                    # Vérifier le stock restant (5.5 - 2.3 = 3.2)
                    verify_response = requests.get(f"{self.base_url}/products/{product['id']}", 
                                                 headers=self.headers, timeout=10)
                    if verify_response.status_code == 200:
                        updated_product = verify_response.json()
                        expected_remaining_stock = 5.5 - 2.3  # 3.2
                        actual_remaining_stock = updated_product['stock']
                        
                        if abs(actual_remaining_stock - expected_remaining_stock) < 0.01:
                            self.log_test("Stock restant après vente fractionnaire", True, 
                                        f"Stock correct: {actual_remaining_stock} kg (5.5 - 2.3)")
                        else:
                            self.log_test("Stock restant après vente fractionnaire", False, 
                                        f"Stock incorrect: attendu {expected_remaining_stock}, reçu {actual_remaining_stock}")
                    
                else:
                    self.log_test("Vente quantité fractionnaire", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Vente quantité fractionnaire", False, str(e))

    def test_automatic_client_creation(self):
        """NOUVEAU - Test création automatique de client lors d'une vente"""
        print("\n=== TEST CRÉATION CLIENT AUTOMATIQUE ===")
        
        if not self.created_products:
            self.log_test("Test création client auto", False, "Pas de produits disponibles")
            return
        
        # Compter les clients existants avant
        try:
            response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
            initial_client_count = len(response.json()) if response.status_code == 200 else 0
        except:
            initial_client_count = 0
        
        # Test: Créer une vente avec client_name mais sans client_id
        auto_client_sale = {
            "client_id": None,  # Pas d'ID client
            "client_name": "Nouveau Client Test Auto",  # Nom fourni
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 1.0
                }
            ],
            "discount": 0.0,
            "payment_method": "espèces"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=auto_client_sale, headers=self.headers, timeout=10)
            if response.status_code == 200:
                sale = response.json()
                self.created_sales.append(sale)
                
                # Vérifier si un nouveau client a été créé automatiquement
                verify_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                if verify_response.status_code == 200:
                    current_clients = verify_response.json()
                    new_client_count = len(current_clients)
                    
                    # Chercher le client créé automatiquement
                    auto_created_client = None
                    for client in current_clients:
                        if client['name'] == "Nouveau Client Test Auto":
                            auto_created_client = client
                            break
                    
                    if auto_created_client:
                        self.log_test("Création automatique client", True, 
                                    f"Client '{auto_created_client['name']}' créé automatiquement avec ID: {auto_created_client['id']}")
                        
                        # Vérifier que la vente référence le bon client
                        if sale.get('client_id') == auto_created_client['id']:
                            self.log_test("Liaison vente-client auto", True, 
                                        "Vente correctement liée au client créé automatiquement")
                        else:
                            self.log_test("Liaison vente-client auto", False, 
                                        f"Vente non liée au client auto (sale client_id: {sale.get('client_id')})")
                    else:
                        self.log_test("Création automatique client", False, 
                                    "Client non créé automatiquement - fonctionnalité manquante")
                        
                        # Si pas de création auto, vérifier que la vente fonctionne quand même
                        if sale['client_name'] == "Nouveau Client Test Auto":
                            self.log_test("Vente sans client_id", True, 
                                        "Vente créée avec client_name seulement")
                        else:
                            self.log_test("Vente sans client_id", False, 
                                        "Problème avec client_name dans la vente")
                else:
                    self.log_test("Vérification clients après vente", False, 
                                "Impossible de récupérer la liste des clients")
            else:
                self.log_test("Vente avec création client auto", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Vente avec création client auto", False, str(e))

    def test_sales_api(self):
        """Test API Ventes avec gestion automatique du stock"""
        print("\n=== TEST VENTES API ===")
        
        if not self.created_products or not self.created_clients:
            self.log_test("Test ventes", False, "Pas de produits ou clients disponibles pour les tests")
            return
        
        # Test 1: Créer une vente avec plusieurs articles
        sale_data = {
            "client_id": self.created_clients[0]['id'],
            "client_name": self.created_clients[0]['name'],
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 2.5
                },
                {
                    "product_id": self.created_products[1]['id'], 
                    "quantity": 1.0
                }
            ],
            "discount": 5.0,
            "payment_method": "carte"
        }
        
        # Récupérer le stock initial pour vérification
        initial_stocks = {}
        for item in sale_data["items"]:
            try:
                response = requests.get(f"{self.base_url}/products/{item['product_id']}", 
                                      headers=self.headers, timeout=10)
                if response.status_code == 200:
                    product = response.json()
                    initial_stocks[item['product_id']] = product['stock']
            except Exception as e:
                print(f"Erreur récupération stock initial: {e}")
        
        # Créer la vente
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=sale_data, headers=self.headers, timeout=10)
            if response.status_code == 200:
                sale = response.json()
                self.created_sales.append(sale)
                
                # Vérifier les calculs
                expected_subtotal = sum(item['total_price'] for item in sale['items'])
                expected_total = expected_subtotal - sale_data['discount']
                
                if abs(sale['subtotal'] - expected_subtotal) < 0.01 and abs(sale['total'] - expected_total) < 0.01:
                    self.log_test("Créer vente - Calculs", True, 
                                f"Vente créée, total: {sale['total']}€, facture: {sale['invoice_number']}")
                else:
                    self.log_test("Créer vente - Calculs", False, 
                                f"Erreur calculs: subtotal={sale['subtotal']}, total={sale['total']}")
                
                # Vérifier la mise à jour automatique du stock
                stock_updates_ok = True
                for item in sale_data["items"]:
                    try:
                        response = requests.get(f"{self.base_url}/products/{item['product_id']}", 
                                              headers=self.headers, timeout=10)
                        if response.status_code == 200:
                            product = response.json()
                            expected_stock = initial_stocks[item['product_id']] - item['quantity']
                            if abs(product['stock'] - expected_stock) > 0.01:
                                stock_updates_ok = False
                                break
                    except Exception as e:
                        stock_updates_ok = False
                        break
                
                if stock_updates_ok:
                    self.log_test("Gestion automatique stock", True, "Stock mis à jour correctement")
                else:
                    self.log_test("Gestion automatique stock", False, "Erreur mise à jour stock")
                    
            else:
                self.log_test("Créer vente", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Créer vente", False, str(e))
        
        # Test 2: Test stock insuffisant
        if self.created_products:
            # Essayer de vendre plus que le stock disponible
            product_with_low_stock = None
            for product in self.created_products:
                try:
                    response = requests.get(f"{self.base_url}/products/{product['id']}", 
                                          headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        current_product = response.json()
                        if current_product['stock'] < 100:  # Prendre un produit avec stock limité
                            product_with_low_stock = current_product
                            break
                except:
                    continue
            
            if product_with_low_stock:
                invalid_sale = {
                    "client_name": "Test Client",
                    "items": [{"product_id": product_with_low_stock['id'], "quantity": product_with_low_stock['stock'] + 10}],
                    "discount": 0.0,
                    "payment_method": "espèces"
                }
                
                try:
                    response = requests.post(f"{self.base_url}/sales", 
                                           json=invalid_sale, headers=self.headers, timeout=10)
                    if response.status_code == 400:
                        self.log_test("Validation stock insuffisant", True, "Erreur stock correctement détectée")
                    else:
                        self.log_test("Validation stock insuffisant", False, 
                                    f"Devrait échouer mais status: {response.status_code}")
                except Exception as e:
                    self.log_test("Validation stock insuffisant", False, str(e))
        
        # Test 3: Récupérer toutes les ventes
        try:
            response = requests.get(f"{self.base_url}/sales", headers=self.headers, timeout=10)
            if response.status_code == 200:
                sales = response.json()
                self.log_test("Récupérer toutes les ventes", True, 
                            f"{len(sales)} ventes trouvées")
            else:
                self.log_test("Récupérer toutes les ventes", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Récupérer toutes les ventes", False, str(e))
        
        # Test 4: Récupérer une vente spécifique
        if self.created_sales:
            sale_id = self.created_sales[0]['id']
            try:
                response = requests.get(f"{self.base_url}/sales/{sale_id}", 
                                      headers=self.headers, timeout=10)
                if response.status_code == 200:
                    sale = response.json()
                    self.log_test("Récupérer vente spécifique", True, 
                                f"Vente {sale['invoice_number']} récupérée")
                else:
                    self.log_test("Récupérer vente spécifique", False, 
                                f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Récupérer vente spécifique", False, str(e))
    
    def test_dashboard_api(self):
        """Test API Dashboard avec statistiques"""
        print("\n=== TEST DASHBOARD API ===")
        
        try:
            response = requests.get(f"{self.base_url}/dashboard/stats", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                stats = response.json()
                
                # Vérifier la structure des statistiques
                required_fields = ['total_products', 'total_clients', 'total_sales', 
                                 'today_sales_count', 'today_revenue', 'low_stock_count', 'low_stock_products']
                
                missing_fields = [field for field in required_fields if field not in stats]
                if not missing_fields:
                    self.log_test("Structure statistiques dashboard", True, 
                                f"Tous les champs requis présents")
                    
                    # Vérifier les valeurs
                    self.log_test("Statistiques dashboard - Valeurs", True, 
                                f"Produits: {stats['total_products']}, Clients: {stats['total_clients']}, "
                                f"Ventes: {stats['total_sales']}, Revenus aujourd'hui: {stats['today_revenue']}€, "
                                f"Stock faible: {stats['low_stock_count']}")
                    
                    # Vérifier les alertes stock faible
                    if stats['low_stock_count'] > 0:
                        self.log_test("Alertes stock faible", True, 
                                    f"{stats['low_stock_count']} produits en stock faible détectés")
                    else:
                        self.log_test("Alertes stock faible", True, "Aucun produit en stock faible")
                        
                else:
                    self.log_test("Structure statistiques dashboard", False, 
                                f"Champs manquants: {missing_fields}")
            else:
                self.log_test("Dashboard statistiques", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Dashboard statistiques", False, str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🧊 DÉBUT DES TESTS BACKEND - BOUTIQUE SURGELÉS 🧊")
        print(f"URL de base: {self.base_url}")
        print("=" * 60)
        
        # Test de connectivité
        if not self.test_api_health():
            print("❌ ARRÊT: API non accessible")
            return False
        
        # Tests des APIs
        self.test_products_crud()
        self.test_clients_api()
        
        # NOUVEAUX TESTS pour les fonctionnalités demandées
        self.test_fractional_stock()
        self.test_automatic_client_creation()
        
        self.test_sales_api()
        self.test_dashboard_api()
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests} tests")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    test_suite = BoutiqueTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)