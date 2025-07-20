# app.py - Moteur de recherche d'articles scientifiques
from flask import Flask, render_template, request, jsonify
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os

app = Flask(__name__)

class ArxivSearcher:
    """Classe pour rechercher des articles sur arXiv"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
    
    def search_articles(self, query, max_results=10):
        """
        Recherche des articles sur arXiv
        
        Args:
            query (str): Terme de recherche
            max_results (int): Nombre maximum de résultats
            
        Returns:
            list: Liste des articles trouvés
        """
        try:
            # Paramètres de la requête
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            # Faire la requête à l'API arXiv
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parser la réponse XML
            articles = self._parse_xml_response(response.content)
            return articles
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def _parse_xml_response(self, xml_content):
        """Parse la réponse XML d'arXiv et extrait les informations des articles"""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace pour arXiv
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Extraire chaque article
            for entry in root.findall('atom:entry', ns):
                article = {}
                
                # Titre
                title_elem = entry.find('atom:title', ns)
                article['title'] = title_elem.text.strip() if title_elem is not None else "Titre non disponible"
                
                # Auteurs
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                article['authors'] = ', '.join(authors) if authors else "Auteur non disponible"
                
                # Résumé
                summary_elem = entry.find('atom:summary', ns)
                article['summary'] = summary_elem.text.strip() if summary_elem is not None else "Résumé non disponible"
                
                # Date de publication
                published_elem = entry.find('atom:published', ns)
                if published_elem is not None:
                    date_str = published_elem.text
                    # Convertir la date ISO en format plus lisible
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        article['date'] = date_obj.strftime('%d/%m/%Y')
                    except:
                        article['date'] = date_str[:10]  # Garde juste YYYY-MM-DD
                else:
                    article['date'] = "Date non disponible"
                
                # Lien vers l'article
                link_elem = entry.find('atom:id', ns)
                article['link'] = link_elem.text if link_elem is not None else "#"
                
                # Catégorie
                category_elem = entry.find('atom:category', ns)
                if category_elem is not None:
                    article['category'] = category_elem.get('term', 'Non catégorisé')
                else:
                    article['category'] = 'Non catégorisé'
                
                articles.append(article)
                
        except Exception as e:
            print(f"Erreur lors du parsing XML: {e}")
            
        return articles

# Instance de notre chercheur d'articles
searcher = ArxivSearcher()

@app.route('/')
def home():
    """Page d'accueil avec le formulaire de recherche"""
    return render_template('index.html')

@app.route('/search')
def search():
    """Endpoint pour effectuer une recherche"""
    query = request.args.get('q', '').strip()
    max_results = int(request.args.get('max_results', 10))
    
    if not query:
        return jsonify({'error': 'Veuillez saisir un terme de recherche'})
    
    # Effectuer la recherche
    articles = searcher.search_articles(query, max_results)
    
    return jsonify({
        'query': query,
        'total_results': len(articles),
        'articles': articles
    })

@app.route('/api/search')
def api_search():
    """API endpoint pour la recherche (pour usage externe)"""
    return search()

if __name__ == '__main__':
    # Configuration pour le déploiement sur Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)