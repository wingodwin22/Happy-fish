#!/usr/bin/env python3
"""
Test spécifique pour la fonctionnalité de création automatique de client lors de vente
Couvre tous les scénarios demandés dans la review request
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://frostbite-sales.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class AutoClientCreationTestSuite:
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
    
    def setup_test_data(self):
        """Créer des produits de test"""
        print("=== SETUP - Création produits de test ===")
        
        test_product = {
            "name": "Produit Test Auto Client",
            "category": "poisson",
            "price": 15.99,
            "stock": 50.0,
            "unit": "kg"
        }
        
        try:
            response = requests.post(f"{self.base_url}/products", 
                                   json=test_product, headers=self.headers, timeout=10)
            if response.status_code == 200:
                product = response.json()
                self.created_products.append(product)
                self.log_test("Setup produit test", True, f"Produit créé: {product['id']}")
                return True
            else:
                self.log_test("Setup produit test", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Setup produit test", False, str(e))
            return False
    
    def test_scenario_1_new_client_creation(self):
        """Test 1: Création client automatique - nouveau client"""
        print("\n=== SCÉNARIO 1: Création automatique nouveau client ===")
        
        if not self.created_products:
            self.log_test("Scénario 1", False, "Pas de produits disponibles")
            return
        
        # Compter les clients avant
        try:
            response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
            initial_clients = response.json() if response.status_code == 200 else []
            initial_count = len(initial_clients)
        except:
            initial_count = 0
        
        # Créer vente avec nouveau client
        sale_data = {
            "client_id": "",  # Vide
            "client_name": "Restaurant La Marine",  # Nouveau nom
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 2.0
                }
            ],
            "discount": 0.0,
            "payment_method": "carte"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=sale_data, headers=self.headers, timeout=10)
            if response.status_code == 200:
                sale = response.json()
                self.created_sales.append(sale)
                
                # Vérifier que le client a été créé
                clients_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                if clients_response.status_code == 200:
                    current_clients = clients_response.json()
                    new_count = len(current_clients)
                    
                    # Chercher le nouveau client
                    new_client = None
                    for client in current_clients:
                        if client['name'] == "Restaurant La Marine":
                            new_client = client
                            break
                    
                    if new_client and new_count > initial_count:
                        self.log_test("Création nouveau client", True, 
                                    f"Client 'Restaurant La Marine' créé avec ID: {new_client['id']}")
                        self.created_clients.append(new_client)
                        
                        # Vérifier que la vente référence le bon client
                        if sale.get('client_id') == new_client['id']:
                            self.log_test("Liaison sale.client_id", True, 
                                        f"Sale.client_id = {sale['client_id']} correspond au nouveau client")
                        else:
                            self.log_test("Liaison sale.client_id", False, 
                                        f"Sale.client_id = {sale.get('client_id')} ne correspond pas au client {new_client['id']}")
                    else:
                        self.log_test("Création nouveau client", False, 
                                    "Client non créé automatiquement")
                else:
                    self.log_test("Vérification clients", False, "Impossible de récupérer les clients")
            else:
                self.log_test("Vente nouveau client", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Vente nouveau client", False, str(e))
    
    def test_scenario_2_existing_client_reuse(self):
        """Test 2: Réutilisation client existant"""
        print("\n=== SCÉNARIO 2: Réutilisation client existant ===")
        
        if not self.created_products:
            self.log_test("Scénario 2", False, "Pas de produits disponibles")
            return
        
        # Créer un client explicitement
        client_data = {
            "name": "Boulangerie Dupont",
            "phone": "01.23.45.67.89",
            "email": "contact@boulangerie-dupont.fr",
            "address": "12 rue du Pain, 75003 Paris",
            "credit_limit": 300.0
        }
        
        try:
            response = requests.post(f"{self.base_url}/clients", 
                                   json=client_data, headers=self.headers, timeout=10)
            if response.status_code == 200:
                existing_client = response.json()
                self.created_clients.append(existing_client)
                self.log_test("Création client existant", True, 
                            f"Client Boulangerie Dupont créé: {existing_client['id']}")
                
                # Compter les clients avant la vente
                clients_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                initial_count = len(clients_response.json()) if clients_response.status_code == 200 else 0
                
                # Créer vente avec le même nom de client
                sale_data = {
                    "client_id": "",  # Vide
                    "client_name": "Boulangerie Dupont",  # Même nom
                    "items": [
                        {
                            "product_id": self.created_products[0]['id'],
                            "quantity": 1.5
                        }
                    ],
                    "discount": 0.0,
                    "payment_method": "espèces"
                }
                
                sale_response = requests.post(f"{self.base_url}/sales", 
                                           json=sale_data, headers=self.headers, timeout=10)
                if sale_response.status_code == 200:
                    sale = sale_response.json()
                    self.created_sales.append(sale)
                    
                    # Vérifier qu'aucun doublon n'a été créé
                    final_clients_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                    if final_clients_response.status_code == 200:
                        final_clients = final_clients_response.json()
                        final_count = len(final_clients)
                        
                        # Compter les clients "Boulangerie Dupont"
                        dupont_clients = [c for c in final_clients if c['name'] == "Boulangerie Dupont"]
                        
                        if final_count == initial_count and len(dupont_clients) == 1:
                            self.log_test("Pas de doublon client", True, 
                                        "Aucun doublon créé, client existant réutilisé")
                            
                            # Vérifier que la vente utilise le client existant
                            if sale.get('client_id') == existing_client['id']:
                                self.log_test("Réutilisation client existant", True, 
                                            f"Vente liée au client existant: {existing_client['id']}")
                            else:
                                self.log_test("Réutilisation client existant", False, 
                                            f"Vente non liée au client existant")
                        else:
                            self.log_test("Pas de doublon client", False, 
                                        f"Doublon détecté: {len(dupont_clients)} clients 'Boulangerie Dupont'")
                    else:
                        self.log_test("Vérification doublons", False, "Impossible de vérifier les doublons")
                else:
                    self.log_test("Vente client existant", False, 
                                f"Status: {sale_response.status_code}")
            else:
                self.log_test("Création client existant", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Scénario 2", False, str(e))
    
    def test_scenario_3_edge_cases(self):
        """Test 3: Cas limites"""
        print("\n=== SCÉNARIO 3: Cas limites ===")
        
        if not self.created_products:
            self.log_test("Scénario 3", False, "Pas de produits disponibles")
            return
        
        # Test 3a: Client Anonyme ne doit PAS créer de client
        sale_anonymous = {
            "client_id": "",
            "client_name": "Client Anonyme",
            "items": [{"product_id": self.created_products[0]['id'], "quantity": 1.0}],
            "discount": 0.0,
            "payment_method": "espèces"
        }
        
        try:
            clients_before = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
            count_before = len(clients_before.json()) if clients_before.status_code == 200 else 0
            
            response = requests.post(f"{self.base_url}/sales", 
                                   json=sale_anonymous, headers=self.headers, timeout=10)
            if response.status_code == 200:
                sale = response.json()
                self.created_sales.append(sale)
                
                clients_after = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                count_after = len(clients_after.json()) if clients_after.status_code == 200 else 0
                
                if count_after == count_before:
                    self.log_test("Client Anonyme - pas de création", True, 
                                "Aucun client créé pour 'Client Anonyme'")
                else:
                    self.log_test("Client Anonyme - pas de création", False, 
                                "Client créé pour 'Client Anonyme' (ne devrait pas)")
            else:
                self.log_test("Vente Client Anonyme", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Test Client Anonyme", False, str(e))
        
        # Test 3b: client_name vide ne doit PAS créer de client
        sale_empty_name = {
            "client_id": "",
            "client_name": "",
            "items": [{"product_id": self.created_products[0]['id'], "quantity": 1.0}],
            "discount": 0.0,
            "payment_method": "carte"
        }
        
        try:
            clients_before = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
            count_before = len(clients_before.json()) if clients_before.status_code == 200 else 0
            
            response = requests.post(f"{self.base_url}/sales", 
                                   json=sale_empty_name, headers=self.headers, timeout=10)
            if response.status_code == 200:
                sale = response.json()
                self.created_sales.append(sale)
                
                clients_after = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                count_after = len(clients_after.json()) if clients_after.status_code == 200 else 0
                
                if count_after == count_before:
                    self.log_test("client_name vide - pas de création", True, 
                                "Aucun client créé pour client_name vide")
                else:
                    self.log_test("client_name vide - pas de création", False, 
                                "Client créé pour client_name vide (ne devrait pas)")
            else:
                self.log_test("Vente client_name vide", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Test client_name vide", False, str(e))
        
        # Test 3c: client_id valide doit utiliser le client fourni
        if self.created_clients:
            existing_client = self.created_clients[0]
            sale_with_id = {
                "client_id": existing_client['id'],
                "client_name": "Nom Différent",  # Nom différent mais ID fourni
                "items": [{"product_id": self.created_products[0]['id'], "quantity": 1.0}],
                "discount": 0.0,
                "payment_method": "crédit"
            }
            
            try:
                response = requests.post(f"{self.base_url}/sales", 
                                       json=sale_with_id, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    sale = response.json()
                    self.created_sales.append(sale)
                    
                    if sale.get('client_id') == existing_client['id']:
                        self.log_test("client_id fourni utilisé", True, 
                                    f"Vente utilise client_id fourni: {existing_client['id']}")
                    else:
                        self.log_test("client_id fourni utilisé", False, 
                                    f"Vente n'utilise pas client_id fourni")
                else:
                    self.log_test("Vente avec client_id", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Test client_id fourni", False, str(e))
    
    def test_scenario_4_complete_integration(self):
        """Test 4: Intégration complète"""
        print("\n=== SCÉNARIO 4: Intégration complète ===")
        
        if not self.created_products:
            self.log_test("Scénario 4", False, "Pas de produits disponibles")
            return
        
        # Récupérer le stock initial
        try:
            product_response = requests.get(f"{self.base_url}/products/{self.created_products[0]['id']}", 
                                          headers=self.headers, timeout=10)
            if product_response.status_code == 200:
                initial_product = product_response.json()
                initial_stock = initial_product['stock']
            else:
                self.log_test("Récupération stock initial", False, "Impossible de récupérer le stock")
                return
        except Exception as e:
            self.log_test("Récupération stock initial", False, str(e))
            return
        
        # Créer vente complète avec nouveau client automatique
        complete_sale = {
            "client_id": "",
            "client_name": "Supermarché Frais Plus",
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 3.5
                }
            ],
            "discount": 10.0,
            "payment_method": "carte"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=complete_sale, headers=self.headers, timeout=10)
            if response.status_code == 200:
                sale = response.json()
                self.created_sales.append(sale)
                
                # Vérifier client créé
                clients_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                if clients_response.status_code == 200:
                    clients = clients_response.json()
                    new_client = None
                    for client in clients:
                        if client['name'] == "Supermarché Frais Plus":
                            new_client = client
                            break
                    
                    if new_client:
                        self.log_test("Client créé intégration", True, 
                                    f"Client 'Supermarché Frais Plus' créé: {new_client['id']}")
                        self.created_clients.append(new_client)
                    else:
                        self.log_test("Client créé intégration", False, "Client non créé")
                
                # Vérifier stock mis à jour
                updated_product_response = requests.get(f"{self.base_url}/products/{self.created_products[0]['id']}", 
                                                      headers=self.headers, timeout=10)
                if updated_product_response.status_code == 200:
                    updated_product = updated_product_response.json()
                    expected_stock = initial_stock - 3.5
                    actual_stock = updated_product['stock']
                    
                    if abs(actual_stock - expected_stock) < 0.01:
                        self.log_test("Stock mis à jour intégration", True, 
                                    f"Stock correct: {actual_stock} (était {initial_stock})")
                    else:
                        self.log_test("Stock mis à jour intégration", False, 
                                    f"Stock incorrect: {actual_stock}, attendu {expected_stock}")
                
                # Vérifier calculs corrects
                expected_item_total = initial_product['price'] * 3.5
                expected_subtotal = expected_item_total
                expected_total = expected_subtotal - 10.0
                
                if (abs(sale['subtotal'] - expected_subtotal) < 0.01 and 
                    abs(sale['total'] - expected_total) < 0.01):
                    self.log_test("Calculs corrects intégration", True, 
                                f"Subtotal: {sale['subtotal']}€, Total: {sale['total']}€")
                else:
                    self.log_test("Calculs corrects intégration", False, 
                                f"Calculs incorrects: subtotal={sale['subtotal']}, total={sale['total']}")
                
            else:
                self.log_test("Vente intégration complète", False, 
                            f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Intégration complète", False, str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests spécifiques"""
        print("🧊 TESTS SPÉCIFIQUES - CRÉATION AUTOMATIQUE CLIENT 🧊")
        print(f"URL de base: {self.base_url}")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_data():
            print("❌ ARRÊT: Impossible de créer les données de test")
            return False
        
        # Tests des scénarios
        self.test_scenario_1_new_client_creation()
        self.test_scenario_2_existing_client_reuse()
        self.test_scenario_3_edge_cases()
        self.test_scenario_4_complete_integration()
        
        # Résumé
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DES TESTS SPÉCIFIQUES")
        print("=" * 70)
        
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
    test_suite = AutoClientCreationTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)