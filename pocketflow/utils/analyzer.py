from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger('ShellAgent')

class CodeAnalyzer:
    """Utility for analyzing code and files"""
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code content"""
        return {
            "lines": len(code.splitlines()),
            "complexity": self.calculate_complexity(code),
            "dependencies": self.find_dependencies(code),
            "suggestions": self.generate_suggestions(code)
        }

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze file content"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            return self.analyze_code(content)
        except Exception as e:
            logger.error(f"Error analyzing file {filepath}: {str(e)}")
            return {"error": str(e)}

    def calculate_complexity(self, code: str) -> int:
        """Calculate code complexity"""
        # Simple complexity calculation based on control structures
        complexity = 1  # Base complexity
        complexity += len(re.findall(r'\bif\b', code))
        complexity += len(re.findall(r'\bfor\b', code))
        complexity += len(re.findall(r'\bwhile\b', code))
        complexity += len(re.findall(r'\bexcept\b', code))
        return complexity

    def find_dependencies(self, code: str) -> List[str]:
        """Find code dependencies"""
        # Look for import statements
        imports = re.findall(r'^import\s+(\w+)', code, re.MULTILINE)
        imports.extend(re.findall(r'^from\s+(\w+)', code, re.MULTILINE))
        return list(set(imports))

    def generate_suggestions(self, code: str) -> List[str]:
        """Generate code improvement suggestions"""
        suggestions = []
        
        # Check for long functions
        if len(code.splitlines()) > 50:
            suggestions.append("Consider breaking down into smaller functions")
            
        # Check for high complexity
        if self.calculate_complexity(code) > 10:
            suggestions.append("Code complexity is high, consider refactoring")
            
        # Check for missing docstrings
        if not re.search(r'""".*?"""', code, re.DOTALL):
            suggestions.append("Consider adding docstrings")
            
        return suggestions

    def log_analysis(self, analysis: Dict[str, Any]) -> None:
        logger.debug(f"Logging analysis: {analysis}") 