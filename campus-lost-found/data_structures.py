from datetime import datetime
from difflib import SequenceMatcher


class Item:
    """Item class to store lost/found items"""
    def __init__(self, item_id, name, desc, category, location, date, user_name, photo=None):
        self.id = item_id
        self.name = name
        self.desc = desc
        self.category = category
        self.location = location
        self.date = date
        self.user_name = user_name
        self.photo = photo


class TrieNode:
    """Trie node for autocomplete"""
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.words = []


class Trie:
    """Trie data structure for autocomplete"""
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            if word.lower() not in node.words:
                node.words.append(word.lower())
        node.is_end = True
    
    def search_prefix(self, prefix):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return sorted(set(node.words))[:10]


class BSTNode:
    """Binary Search Tree Node"""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


class BST:
    """Binary Search Tree for organizing items by category"""
    def __init__(self):
        self.root = None
    
    def insert(self, key, value):
        if self.root is None:
            self.root = BSTNode(key, value)
        else:
            self._insert_recursive(self.root, key, value)
    
    def _insert_recursive(self, node, key, value):
        if key < node.key:
            if node.left is None:
                node.left = BSTNode(key, value)
            else:
                self._insert_recursive(node.left, key, value)
        else:
            if node.right is None:
                node.right = BSTNode(key, value)
            else:
                self._insert_recursive(node.right, key, value)
    
    def get_all(self):
        result = []
        self._inorder_traversal(self.root, result)
        return result
    
    def _inorder_traversal(self, node, result):
        if node:
            self._inorder_traversal(node.left, result)
            result.append(node.value)
            self._inorder_traversal(node.right, result)


class LostAndFoundMatcher:
    """Main system for managing lost and found items"""
    def __init__(self):
        self.lost_items = {}
        self.found_items = {}
        self.lost_trie = Trie()
        self.found_trie = Trie()
        self.lost_bst = BST()
        self.found_bst = BST()
        self.lost_counter = 0
        self.found_counter = 0
    
    def add_lost_item(self, name, desc, category, location, date, user_name, photo=None):
        self.lost_counter += 1
        item_id = f"L{self.lost_counter:03d}"
        
        item = Item(item_id, name, desc, category, location, date, user_name, photo)
        self.lost_items[item_id] = item
        
        # Add to Trie
        self.lost_trie.insert(name)
        
        # Add to BST
        self.lost_bst.insert(category, item)
        
        return item_id
    
    def add_found_item(self, name, desc, category, location, date, user_name, photo=None):
        self.found_counter += 1
        item_id = f"F{self.found_counter:03d}"
        
        item = Item(item_id, name, desc, category, location, date, user_name, photo)
        self.found_items[item_id] = item
        
        # Add to Trie
        self.found_trie.insert(name)
        
        # Add to BST
        self.found_bst.insert(category, item)
        
        return item_id
    
    def get_autocomplete_suggestions(self, prefix, item_type='lost'):
        if item_type == 'lost':
            return self.lost_trie.search_prefix(prefix)
        else:
            return self.found_trie.search_prefix(prefix)
    
    def calculate_similarity(self, item1, item2):
        """Calculate similarity score between two items"""
        score = 0
        
        # Name similarity (40%)
        name_sim = SequenceMatcher(None, item1.name.lower(), item2.name.lower()).ratio()
        score += name_sim * 40
        
        # Description similarity (20%)
        desc_sim = SequenceMatcher(None, item1.desc.lower(), item2.desc.lower()).ratio()
        score += desc_sim * 20
        
        # Category match (20%)
        if item1.category.lower() == item2.category.lower():
            score += 20
        
        # Location match (15%)
        if item1.location.lower() == item2.location.lower():
            score += 15
        
        # Date proximity (5%)
        try:
            date1 = datetime.strptime(item1.date, '%Y-%m-%d')
            date2 = datetime.strptime(item2.date, '%Y-%m-%d')
            days_diff = abs((date1 - date2).days)
            if days_diff <= 7:
                score += 5 * (1 - days_diff / 7)
        except:
            pass
        
        return int(score)
    
    def find_matches(self, item_id, is_lost=True):
        """Find potential matches for an item"""
        if is_lost:
            source_items = self.lost_items
            target_items = self.found_items
        else:
            source_items = self.found_items
            target_items = self.lost_items
        
        if item_id not in source_items:
            return []
        
        source_item = source_items[item_id]
        matches = []
        
        for target_id, target_item in target_items.items():
            score = self.calculate_similarity(source_item, target_item)
            if score >= 30:  # Minimum threshold
                matches.append({
                    'item': target_item,
                    'score': score
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def get_all_categories(self, item_type='lost'):
        """Get all unique categories"""
        if item_type == 'lost':
            items = self.lost_items.values()
        else:
            items = self.found_items.values()
        
        categories = set()
        for item in items:
            categories.add(item.category)
        return sorted(categories)
