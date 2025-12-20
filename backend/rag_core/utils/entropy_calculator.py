import math
from collections import Counter
from typing import Dict, Any

class EntropyCalculator:
    """
    Calculate Shannon entropy for:
    1. Query complexity analysis - measure query diversity
    2. Password strength analysis - measure password randomness
    
    Higher entropy = more complex/diverse/secure
    
    Optimizations:
    - O(n) character counting with Counter
    - Character-level entropy (faster than word-level for long queries)
    - Set operations for diversity (O(n))
    - No API calls - purely local computation
    """
    
    def __init__(self):
        self.thresholds = {
            'simple': 0.5,    # Low entropy queries
            'medium': 0.7,    # Medium complexity
            'complex': 0.7    # High entropy queries
        }
        self.password_thresholds = {
            'weak': 2.5,      # Below this = weak
            'medium': 3.5,    # Below this = medium
            'strong': 4.0     # Above this = strong
        }
    
    def calculate_shannon_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy: H(X) = -Σ p(x) * log2(p(x))
        Normalized to [0, 1] range
        
        Time Complexity: O(n) where n = text length
        Space Complexity: O(k) where k = unique characters
        """
        if not text:
            return 0.0
        
        # Count character frequencies - O(n)
        char_counts = Counter(text.lower())
        total_chars = len(text)
        
        # Calculate entropy - O(k) where k = unique chars
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total_chars
            entropy -= probability * math.log2(probability)
        
        # Normalize to [0, 1]
        max_entropy = math.log2(len(char_counts)) if len(char_counts) > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return normalized_entropy
    
    def analyze_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Analyze password strength using Shannon entropy.
        
        A strong password has:
        - High entropy (randomness)
        - Mix of character types (upper, lower, digits, symbols)
        - Sufficient length
        
        Returns strength assessment and recommendations.
        """
        if not password:
            return {
                'entropy': 0,
                'strength': 'none',
                'score': 0,
                'analysis': 'No password provided',
                'recommendations': ['Provide a password to analyze']
            }
        
        # Calculate raw entropy (not normalized)
        char_counts = Counter(password)
        total_chars = len(password)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total_chars
            entropy -= probability * math.log2(probability)
        
        # Character type analysis
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        char_types = sum([has_upper, has_lower, has_digit, has_symbol])
        
        # Length factor
        length = len(password)
        length_score = min(length / 16, 1.0)  # Max score at 16 chars
        
        # Calculate overall score (0-100)
        entropy_score = min(entropy / 4.5, 1.0) * 40  # Max 40 points
        type_score = (char_types / 4) * 30           # Max 30 points
        length_points = length_score * 30            # Max 30 points
        total_score = entropy_score + type_score + length_points
        
        # Determine strength
        if total_score < 30:
            strength = 'weak'
        elif total_score < 50:
            strength = 'fair'
        elif total_score < 70:
            strength = 'medium'
        elif total_score < 85:
            strength = 'strong'
        else:
            strength = 'very_strong'
        
        # Generate recommendations
        recommendations = []
        if length < 12:
            recommendations.append(f'Increase length (current: {length}, recommended: 12+)')
        if not has_upper:
            recommendations.append('Add uppercase letters (A-Z)')
        if not has_lower:
            recommendations.append('Add lowercase letters (a-z)')
        if not has_digit:
            recommendations.append('Add numbers (0-9)')
        if not has_symbol:
            recommendations.append('Add symbols (!@#$%^&*)')
        if entropy < 3.0:
            recommendations.append('Use more varied characters to increase randomness')
        
        if not recommendations:
            recommendations.append('Password meets all security criteria!')
        
        return {
            'entropy': round(entropy, 3),
            'strength': strength,
            'score': round(total_score, 1),
            'length': length,
            'char_types': char_types,
            'has_upper': has_upper,
            'has_lower': has_lower,
            'has_digit': has_digit,
            'has_symbol': has_symbol,
            'analysis': f'Entropy: {entropy:.2f} bits, {char_types}/4 character types, {length} chars',
            'recommendations': recommendations
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Comprehensive query analysis with tool recommendations
        
        Returns:
            - entropy: Shannon entropy score (0-1)
            - complexity: simple/medium/complex
            - char_diversity: unique chars / total chars
            - word_count: number of words
            - unique_words: number of unique words
            - recommendations: suggested tools to use
            - reasoning: explanation of recommendations
        """
        entropy = self.calculate_shannon_entropy(query)
        
        # Additional metrics - all O(n)
        words = query.lower().split()
        word_count = len(words)
        unique_words = len(set(words))
        char_diversity = len(set(query.lower())) / len(query) if query else 0
        
        # Determine complexity
        if entropy < self.thresholds['simple']:
            complexity = 'simple'
        elif entropy < self.thresholds['complex']:
            complexity = 'medium'
        else:
            complexity = 'complex'
        
        # Tool recommendations based on analysis
        recommendations = self._recommend_tools(
            entropy, complexity, word_count, unique_words, query
        )
        
        return {
            'entropy': entropy,
            'complexity': complexity,
            'char_diversity': char_diversity,
            'word_count': word_count,
            'unique_words': unique_words,
            'recommendations': recommendations['tools'],
            'reasoning': recommendations['reasoning']
        }
    
    def _recommend_tools(
        self, 
        entropy: float, 
        complexity: str, 
        word_count: int,
        unique_words: int,
        query: str
    ) -> Dict[str, Any]:
        """
        Recommend which RAG tools to use based on query characteristics
        
        Time Complexity: O(k*m) where k = keywords, m = query length
        (Faster than embedding-based similarity which requires API calls)
        """
        tools = []
        reasoning_parts = []
        
        # Check for entity/relationship keywords -> Graph Search
        # O(k*m) keyword matching
        graph_keywords = ['how', 'what', 'relate', 'connect', 'relationship', 
                          'protocol', 'uses', 'includes', 'affects']
        if any(kw in query.lower() for kw in graph_keywords):
            tools.append('graph_search')
            reasoning_parts.append("Query asks about relationships/entities (graph keywords detected)")
        
        # Check for implementation/detail keywords -> Parent-Child Search
        detail_keywords = ['implement', 'configure', 'setup', 'example', 'code',
                          'steps', 'complete', 'detailed', 'full']
        if any(kw in query.lower() for kw in detail_keywords):
            tools.append('parent_child_search')
            reasoning_parts.append("Query asks for implementation details (detail keywords detected)")
        
        # High entropy + many unique words -> Use multiple tools
        if entropy > 0.7 and unique_words > 8:
            if 'graph_search' not in tools:
                tools.append('graph_search')
            if 'parent_child_search' not in tools:
                tools.append('parent_child_search')
            reasoning_parts.append(f"High complexity (entropy={entropy:.2f}, unique_words={unique_words})")
        
        # Fallback: if no tools selected, use parent-child (most comprehensive)
        if not tools:
            tools.append('parent_child_search')
            reasoning_parts.append("Default to parent-child for general questions")
        
        # Format tools as string
        tools_str = ", ".join(tools)
        reasoning_str = "; ".join(reasoning_parts)
        
        return {
            'tools': tools_str,
            'reasoning': reasoning_str
        }

