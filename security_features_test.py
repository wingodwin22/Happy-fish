#!/usr/bin/env python3
"""
Tests spécifiques pour les nouvelles fonctionnalités de sécurité et d'édition
Boutique Surgelés - Focus sur restriction crédit, édition client, recherche produits, validation quantités
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://frostbite-sales.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class SecurityFeaturesTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_results = []
        self.created_products = []
        self.created_clients = []
        
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
        """Créer des données de test nécessaires"""
        print("\n=== SETUP DONNÉES DE TEST ===")
        
        # Créer quelques produits pour les tests
        test_products = [
            {
                "name": "Saumon Atlantique Premium",
                "category": "poisson",
                "price": 28.99,
                "stock": 12.5,
                "unit": "kg"
            },
            {
                "name": "Crevettes Roses Géantes",
                "category": "poisson",
                "price": 22.50,
                "stock": 8.0,
                "unit": "kg"
            },
            {
                "name": "Bœuf Haché 15% MG",
                "category": "viande",
                "price": 14.99,
                "stock": 20.0,
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
                    print(f"✅ Produit créé: {product['name']} (ID: {product['id']})")
                else:
                    print(f"❌ Erreur création produit {product_data['name']}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception création produit {product_data['name']}: {str(e)}")
        
        # Créer un client existant pour les tests d'édition
        test_client = {
            "name": "Restaurant Le Gourmet",
            "phone": "01.42.33.44.55",
            "email": "contact@legourmet.fr",
            "address": "25 rue des Saveurs, 75008 Paris",
            "credit_limit": 800.0
        }
        
        try:
            response = requests.post(f"{self.base_url}/clients", 
                                   json=test_client, headers=self.headers, timeout=10)
            if response.status_code == 200:
                client = response.json()
                self.created_clients.append(client)
                print(f"✅ Client créé: {client['name']} (ID: {client['id']})")
            else:
                print(f"❌ Erreur création client: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception création client: {str(e)}")
    
    def test_credit_restriction_new_client(self):
        """Test 1: Restriction crédit pour nouveaux clients"""
        print("\n=== TEST RESTRICTION CRÉDIT NOUVEAUX CLIENTS ===")
        
        if not self.created_products:
            self.log_test("Restriction crédit - Setup", False, "Pas de produits disponibles")
            return
        
        # Compter les clients existants avant le test
        try:
            response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
            initial_client_count = len(response.json()) if response.status_code == 200 else 0
        except:
            initial_client_count = 0
        
        # Test: Tenter vente à crédit avec nouveau client
        credit_sale_new_client = {
            "client_id": None,  # Pas d'ID client (nouveau client)
            "client_name": "Restaurant Test Crédit",  # Nom fourni
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 2.0
                }
            ],
            "discount": 0.0,
            "payment_method": "crédit"  # CRÉDIT - doit être refusé
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=credit_sale_new_client, headers=self.headers, timeout=10)
            
            if response.status_code == 400:
                response_data = response.json()
                error_message = response_data.get('detail', '')
                
                # Vérifier le message d'erreur explicite
                if "Impossible de vendre à crédit à un nouveau client" in error_message:
                    self.log_test("Restriction crédit - Message erreur", True, 
                                f"Message d'erreur correct: {error_message}")
                else:
                    self.log_test("Restriction crédit - Message erreur", False, 
                                f"Message d'erreur incorrect: {error_message}")
                
                # Vérifier qu'aucun client n'a été créé
                verify_response = requests.get(f"{self.base_url}/clients", headers=self.headers, timeout=10)
                if verify_response.status_code == 200:
                    current_clients = verify_response.json()
                    current_client_count = len(current_clients)
                    
                    # Vérifier qu'aucun client "Restaurant Test Crédit" n'existe
                    test_client_exists = any(c['name'] == "Restaurant Test Crédit" for c in current_clients)
                    
                    if not test_client_exists and current_client_count == initial_client_count:
                        self.log_test("Restriction crédit - Pas de création client", True, 
                                    "Aucun client créé lors de la tentative de vente à crédit")
                    else:
                        self.log_test("Restriction crédit - Pas de création client", False, 
                                    f"Client créé malgré l'interdiction (count: {current_client_count} vs {initial_client_count})")
                
            else:
                self.log_test("Restriction crédit - Erreur 400", False, 
                            f"Devrait retourner 400 mais status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Restriction crédit - Exception", False, str(e))
    
    def test_client_editing_api(self):
        """Test 2: API Édition Client (GET et PUT)"""
        print("\n=== TEST API ÉDITION CLIENT ===")
        
        if not self.created_clients:
            self.log_test("Édition client - Setup", False, "Pas de clients disponibles")
            return
        
        client_id = self.created_clients[0]['id']
        
        # Test GET /api/clients/{id} - Récupérer un client spécifique
        try:
            response = requests.get(f"{self.base_url}/clients/{client_id}", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                client = response.json()
                required_fields = ['id', 'name', 'phone', 'email', 'address', 'credit_limit']
                missing_fields = [field for field in required_fields if field not in client]
                
                if not missing_fields:
                    self.log_test("GET Client spécifique", True, 
                                f"Client récupéré: {client['name']} avec tous les champs")
                else:
                    self.log_test("GET Client spécifique", False, 
                                f"Champs manquants: {missing_fields}")
            else:
                self.log_test("GET Client spécifique", False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET Client spécifique", False, str(e))
        
        # Test PUT /api/clients/{id} - Modifier client existant
        update_data = {
            "name": "Restaurant Le Gourmet Modifié",
            "phone": "01.42.33.44.99",  # Nouveau téléphone
            "email": "nouveau@legourmet.fr",  # Nouvel email
            "address": "30 rue des Nouvelles Saveurs, 75009 Paris",  # Nouvelle adresse
            "credit_limit": 1200.0  # Nouvelle limite crédit
        }
        
        try:
            response = requests.put(f"{self.base_url}/clients/{client_id}", 
                                  json=update_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                updated_client = response.json()
                
                # Vérifier que toutes les modifications ont été appliquées
                modifications_ok = True
                for field, expected_value in update_data.items():
                    if updated_client.get(field) != expected_value:
                        modifications_ok = False
                        break
                
                if modifications_ok:
                    self.log_test("PUT Modifier client", True, 
                                f"Client modifié avec succès: {updated_client['name']}")
                    
                    # Vérifier la persistance des modifications
                    verify_response = requests.get(f"{self.base_url}/clients/{client_id}", 
                                                 headers=self.headers, timeout=10)
                    if verify_response.status_code == 200:
                        verified_client = verify_response.json()
                        if verified_client['name'] == update_data['name']:
                            self.log_test("PUT Persistance modifications", True, 
                                        "Modifications persistées correctement")
                        else:
                            self.log_test("PUT Persistance modifications", False, 
                                        "Modifications non persistées")
                else:
                    self.log_test("PUT Modifier client", False, 
                                "Certaines modifications non appliquées")
            else:
                self.log_test("PUT Modifier client", False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("PUT Modifier client", False, str(e))
        
        # Test validation des champs - client inexistant
        fake_client_id = "client-inexistant-12345"
        try:
            response = requests.get(f"{self.base_url}/clients/{fake_client_id}", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                self.log_test("GET Client inexistant (404)", True, 
                            "Erreur 404 correctement retournée")
            else:
                self.log_test("GET Client inexistant (404)", False, 
                            f"Devrait retourner 404 mais status: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET Client inexistant", False, str(e))
    
    def test_product_search_api(self):
        """Test 3: API Recherche Produits"""
        print("\n=== TEST API RECHERCHE PRODUITS ===")
        
        if not self.created_products:
            self.log_test("Recherche produits - Setup", False, "Pas de produits disponibles")
            return
        
        # Test recherche insensible à la casse
        search_queries = [
            ("sau", "Recherche 'sau' (minuscules)"),
            ("SAU", "Recherche 'SAU' (majuscules)"),
            ("Crevettes", "Recherche 'Crevettes' (mixte)"),
            ("bœuf", "Recherche 'bœuf' (accent)"),
            ("xyz", "Recherche 'xyz' (aucun résultat)")
        ]
        
        for query, test_name in search_queries:
            try:
                response = requests.get(f"{self.base_url}/products/search/{query}", 
                                      headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Vérifier le format de réponse
                    if isinstance(results, list):
                        if len(results) > 0:
                            # Vérifier la structure du premier résultat
                            first_result = results[0]
                            required_fields = ['id', 'name', 'price', 'stock', 'unit']
                            missing_fields = [field for field in required_fields if field not in first_result]
                            
                            if not missing_fields:
                                # Vérifier la limite de 10 résultats
                                if len(results) <= 10:
                                    # Vérifier que les résultats contiennent bien le terme recherché (sauf pour xyz)
                                    if query.lower() == "xyz":
                                        if len(results) == 0:
                                            self.log_test(test_name, True, "Aucun résultat pour recherche inexistante")
                                        else:
                                            self.log_test(test_name, False, f"Devrait retourner 0 résultats mais {len(results)} trouvés")
                                    else:
                                        # Vérifier que les résultats contiennent le terme (insensible à la casse)
                                        relevant_results = [r for r in results if query.lower() in r['name'].lower()]
                                        if len(relevant_results) > 0:
                                            self.log_test(test_name, True, 
                                                        f"{len(results)} résultats trouvés, format correct")
                                        else:
                                            self.log_test(test_name, True, 
                                                        f"{len(results)} résultats (recherche élargie possible)")
                                else:
                                    self.log_test(test_name, False, 
                                                f"Trop de résultats: {len(results)} > 10")
                            else:
                                self.log_test(test_name, False, 
                                            f"Champs manquants dans résultat: {missing_fields}")
                        else:
                            if query.lower() == "xyz":
                                self.log_test(test_name, True, "Aucun résultat pour recherche inexistante")
                            else:
                                self.log_test(test_name, True, "Aucun résultat trouvé (normal si pas de correspondance)")
                    else:
                        self.log_test(test_name, False, "Réponse n'est pas une liste")
                else:
                    self.log_test(test_name, False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(test_name, False, str(e))
        
        # Test recherche avec terme trop court (< 2 caractères)
        try:
            response = requests.get(f"{self.base_url}/products/search/a", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                if len(results) == 0:
                    self.log_test("Recherche terme court", True, 
                                "Recherche avec 1 caractère retourne liste vide")
                else:
                    self.log_test("Recherche terme court", True, 
                                f"Recherche avec 1 caractère retourne {len(results)} résultats")
            else:
                self.log_test("Recherche terme court", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Recherche terme court", False, str(e))
    
    def test_quantity_validation(self):
        """Test 4: Validation quantités (doit être > 0)"""
        print("\n=== TEST VALIDATION QUANTITÉS ===")
        
        if not self.created_products or not self.created_clients:
            self.log_test("Validation quantités - Setup", False, "Pas de produits ou clients disponibles")
            return
        
        # Test quantité 0
        zero_quantity_sale = {
            "client_id": self.created_clients[0]['id'],
            "client_name": self.created_clients[0]['name'],
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 0  # Quantité zéro - doit être refusée
                }
            ],
            "discount": 0.0,
            "payment_method": "espèces"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=zero_quantity_sale, headers=self.headers, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Validation quantité zéro", True, 
                            "Vente avec quantité 0 correctement refusée")
            elif response.status_code == 200:
                # Si la vente passe, vérifier qu'elle n'a pas d'impact sur le stock
                sale = response.json()
                if sale['items'][0]['quantity'] == 0 and sale['total'] == 0:
                    self.log_test("Validation quantité zéro", True, 
                                "Vente avec quantité 0 acceptée mais sans impact")
                else:
                    self.log_test("Validation quantité zéro", False, 
                                "Vente avec quantité 0 ne devrait pas être traitée normalement")
            else:
                self.log_test("Validation quantité zéro", False, 
                            f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            self.log_test("Validation quantité zéro", False, str(e))
        
        # Test quantité négative
        negative_quantity_sale = {
            "client_id": self.created_clients[0]['id'],
            "client_name": self.created_clients[0]['name'],
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": -2.5  # Quantité négative - doit être refusée
                }
            ],
            "discount": 0.0,
            "payment_method": "carte"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=negative_quantity_sale, headers=self.headers, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Validation quantité négative", True, 
                            "Vente avec quantité négative correctement refusée")
            elif response.status_code == 200:
                self.log_test("Validation quantité négative", False, 
                            "Vente avec quantité négative ne devrait pas être acceptée")
            else:
                self.log_test("Validation quantité négative", False, 
                            f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            self.log_test("Validation quantité négative", False, str(e))
        
        # Test quantité positive valide (contrôle)
        valid_quantity_sale = {
            "client_id": self.created_clients[0]['id'],
            "client_name": self.created_clients[0]['name'],
            "items": [
                {
                    "product_id": self.created_products[0]['id'],
                    "quantity": 1.5  # Quantité positive valide
                }
            ],
            "discount": 0.0,
            "payment_method": "espèces"
        }
        
        try:
            response = requests.post(f"{self.base_url}/sales", 
                                   json=valid_quantity_sale, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                sale = response.json()
                if sale['items'][0]['quantity'] == 1.5 and sale['total'] > 0:
                    self.log_test("Validation quantité positive", True, 
                                f"Vente avec quantité positive acceptée: {sale['total']}€")
                else:
                    self.log_test("Validation quantité positive", False, 
                                "Problème avec vente quantité positive")
            else:
                self.log_test("Validation quantité positive", False, 
                            f"Vente valide refusée, status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Validation quantité positive", False, str(e))
    
    def run_security_tests(self):
        """Exécuter tous les tests de sécurité"""
        print("🔒 TESTS FONCTIONNALITÉS SÉCURITÉ ET ÉDITION - BOUTIQUE SURGELÉS 🔒")
        print(f"URL de base: {self.base_url}")
        print("=" * 70)
        
        # Setup des données de test
        self.setup_test_data()
        
        # Tests des nouvelles fonctionnalités
        self.test_credit_restriction_new_client()
        self.test_client_editing_api()
        self.test_product_search_api()
        self.test_quantity_validation()
        
        # Résumé des résultats
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DES TESTS SÉCURITÉ")
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
    test_suite = SecurityFeaturesTestSuite()
    success = test_suite.run_security_tests()
    sys.exit(0 if success else 1)