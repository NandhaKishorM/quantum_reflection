import numpy as np
from transformers import AutoTokenizer, LlamaForCausalLM
import torch
from scipy.linalg import expm
from typing import List, Tuple, Dict, Optional, Union
import nltk
from nltk.tokenize import sent_tokenize
import re
nltk.download('punkt')

class GeneralQuantumSolver:
    def __init__(self, 
                 model_path: str = "unsloth/Meta-Llama-3.1-8B-Instruct", 
                 dimension: int = 512,
                 domain: Optional[str] = None):
        """
        Initialize the general quantum problem solver.
        
        Args:
            model_path: Path to the language model to use
            dimension: Dimension of the quantum state space
            domain: Optional specific mathematical domain (e.g., "algebra", "calculus", "number_theory")
        """
        self.dimension = dimension
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.domain = domain
        
        # Load model components
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        self.model = LlamaForCausalLM.from_pretrained(model_path, device_map="auto")
        
        # Quantum components
        self.quantum_state = np.zeros(dimension, dtype=complex)
        
        # Solver parameters
        self.max_iterations = 5
        self.convergence_threshold = 0.98
        self.stability_window = 3
        self.stability_threshold = 0.001
        
        # Solution tracking
        self.solution_history = []
        self.convergence_history = []
        self.solution_found = False
        
        # Initialize system prompt based on domain
        self._initialize_system_prompt()

    def _initialize_system_prompt(self):
        """Initialize the system prompt based on the mathematical domain."""
        base_prompt = """You are a precise mathematical problem solver. When solving problems:

1. Break down the solution into clearly numbered steps
2. Format each step as: 
   Step N: [Brief title]
   [Detailed mathematical work]
   ∴ [Conclusion of this step]
3. Use rigorous mathematical notation
4. Justify each significant step
5. Highlight key insights with '→ Insight:'
6. End with a clearly stated conclusion

For each step:
- Show all work clearly
- Explain why the step is needed
- Note any assumptions made
- Highlight potential pitfalls"""

        # Add domain-specific guidelines if a domain is specified
        domain_guidelines = {
            "algebra": """
Additional Guidelines for Algebra:
- State all variable definitions clearly
- Show complete factorization steps
- Identify special patterns (perfect squares, difference of squares, etc.)
- Verify solutions by substitution when applicable""",

            "calculus": """
Additional Guidelines for Calculus:
- State all differentiation and integration rules used
- Show intermediate steps in chain rule applications
- Verify critical points and extrema
- Include domain and range analysis""",

            "number_theory": """
Additional Guidelines for Number Theory:
- State all theorems used
- Show complete prime factorizations when relevant
- Provide clear modular arithmetic calculations
- Include divisibility analysis when appropriate""",

            "geometry": """
Additional Guidelines for Geometry:
- Include clear diagrams when needed
- State all theorems and postulates used
- Show angle calculations explicitly
- Verify triangle inequalities when applicable"""
        }

        self.system_prompt = base_prompt
        if self.domain and self.domain.lower() in domain_guidelines:
            self.system_prompt += "\n\n" + domain_guidelines[self.domain.lower()]

    def check_solution_stability(self, current_solution: str) -> bool:
        """Check if the solution has stabilized over recent iterations."""
        if len(self.solution_history) < self.stability_window:
            self.solution_history.append(current_solution)
            return False
            
        # Compare with previous solutions
        self.solution_history.append(current_solution)
        recent_solutions = self.solution_history[-self.stability_window:]
        
        # Extract numerical values and key mathematical terms
        def extract_key_elements(sol: str) -> set:
            numbers = set(re.findall(r'-?\d*\.?\d+', sol))
            math_terms = set(re.findall(r'[α-ω\+\-\*/\^\{\}\[\]]+', sol))
            return numbers.union(math_terms)
            
        solution_elements = [extract_key_elements(sol) for sol in recent_solutions]
        
        # Check if solutions have stabilized
        is_stable = all(
            len(solution_elements[i].symmetric_difference(solution_elements[i-1])) / 
            max(len(solution_elements[i]), 1) < self.stability_threshold
            for i in range(1, len(solution_elements))
        )
        
        # Remove oldest solution if window is full
        if len(self.solution_history) > self.stability_window:
            self.solution_history.pop(0)
            
        return is_stable

    def extract_solution_steps(self, response: str) -> List[str]:
        """Extract individual solution steps from the response."""
        steps = re.split(r'Step \d+[:.]\s+', response)[1:]
        return [step.strip() for step in steps]

    def analyze_step_complexity(self, step: str) -> float:
        """Analyze the mathematical complexity of a solution step."""
        # Count mathematical symbols and expressions
        math_symbols = len(re.findall(r'[+\-*/^√∑∏∫∂θπ=≠≤≥∈∉⊆⊂∪∩]', step))
        equations = len(re.findall(r'[^=]=[^=]', step))
        variables = len(set(re.findall(r'[a-zA-Z]', step)))
        
        # Weight different components
        complexity = (math_symbols * 0.4 + equations * 0.4 + variables * 0.2) / 100
        return min(max(complexity, 0.1), 1.0)

    def create_step_reflection_prompt(self, step: str, step_number: int, total_steps: int, 
                                    quantum_state: np.ndarray) -> str:
        """Create a reflection prompt for a specific solution step."""
        step_complexity = self.analyze_step_complexity(step)
        
        return f"""
        {self.system_prompt}

        Please analyze and improve Step {step_number} of {total_steps}:

        Current Step:
        {step}

        Consider:
        1. Is the mathematical reasoning complete and rigorous?
        2. Are calculations shown clearly and correctly?
        3. Are edge cases and conditions addressed?
        4. Could the explanation be more precise?
        5. Is this step necessary and well-connected to others?

        Analysis Metrics:
        - Step Complexity: {step_complexity:.2f}
        - Quantum Certainty: {np.abs(quantum_state).mean():.2f}

        Provide an improved version of this step:
        Step {step_number}: """

    def create_steps_integration_prompt(self, steps: List[str], quantum_state: np.ndarray) -> str:
        """Create a prompt for integrating multiple solution steps."""
        steps_text = "\n\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
        return f"""
        {self.system_prompt}

        Review these solution steps:

        {steps_text}

        Consider:
        1. Logical flow between steps
        2. Completeness of reasoning
        3. Clarity of progression
        4. Supporting evidence for conclusions
        5. Overall solution coherence

        Coherence Measure: {np.abs(quantum_state).mean():.2f}

        Provide an improved integrated solution:
        """

    def generate_with_reflection(self, prompt: str, max_new_tokens: int = 2000) -> Dict:
        """Generate solution with quantum reflection."""
        print("\n=== Starting Step-by-Step Mathematical Analysis ===")
        print("\nInitial Prompt:")
        print(prompt)
        
        # Initial solution generation
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        
        print("\nGenerating initial solution...")
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                temperature=0.1,
                do_sample=True
            )
        
        initial_response = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=True)
        print("\nInitial Response:")
        print(initial_response)
        
        current_steps = self.extract_solution_steps(initial_response)
        print("\nExtracted Steps:")
        for i, step in enumerate(current_steps, 1):
            print(f"\nStep {i}:")
            print(step)
            complexity = self.analyze_step_complexity(step)
            print(f"Step Complexity: {complexity:.3f}")
        
        improved_steps = []
        quantum_states = []
        consecutive_stable_iterations = 0
        
        for iteration in range(self.max_iterations):
            print(f"\n=== Reflection Iteration {iteration + 1} ===")
            
            current_solution = " ".join(current_steps)
            print("\nCurrent Complete Solution:")
            print(current_solution)
            
            stability = self.check_solution_stability(current_solution)
            print(f"\nSolution Stability Check: {'Stable' if stability else 'Not Stable'}")
            
            if stability:
                consecutive_stable_iterations += 1
                print(f"Consecutive stable iterations: {consecutive_stable_iterations}")
                if consecutive_stable_iterations >= self.stability_window:
                    print("\n=== Solution Stabilized ===")
                    break
            else:
                consecutive_stable_iterations = 0
            
            print("\nProcessing individual steps:")
            for i, step in enumerate(current_steps):
                print(f"\nAnalyzing Step {i+1}:")
                print("Original step:", step)
                
                current_state = self.apply_quantum_operation(step)
                quantum_states.append(current_state)
                print(f"Quantum state mean amplitude: {np.abs(current_state).mean():.4f}")
                
                reflection_prompt = self.create_step_reflection_prompt(
                    step, i+1, len(current_steps), current_state
                )
                print("\nReflection Prompt:")
                print(reflection_prompt)
                
                inputs = self.tokenizer.encode(reflection_prompt, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=max_new_tokens,
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True
                    )
                
                improved_step = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=True)
                improved_steps.append(improved_step)
                
                print("\nImproved step:")
                print(improved_step)
                
                step_quantum_state = self.apply_quantum_operation(improved_step)
                step_fidelity = self.measure_convergence(current_state, step_quantum_state)
                self.convergence_history.append(step_fidelity)
                
                print(f"Step fidelity: {step_fidelity:.4f}")
                
                if len(self.convergence_history) >= 3:
                    recent_convergence = self.convergence_history[-3:]
                    print(f"Recent convergence history: {recent_convergence}")
                    if (max(recent_convergence) - min(recent_convergence) < self.stability_threshold and
                        np.mean(recent_convergence) > self.convergence_threshold):
                        print(f"\n=== Step {i+1} Converged ===")
                        continue
            
            integration_state = self.apply_quantum_operation(" ".join(improved_steps))
            print("\nIntegration state mean amplitude:", np.abs(integration_state).mean())
            
            if iteration > 0:
                overall_convergence = self.measure_convergence(
                    quantum_states[-len(current_steps):],
                    quantum_states[-2*len(current_steps):-len(current_steps)]
                )
                
                print(f"\nOverall convergence: {overall_convergence:.4f}")
                
                if (overall_convergence > self.convergence_threshold and 
                    consecutive_stable_iterations >= self.stability_window - 1):
                    print("\n=== Overall Solution Converged ===")
                    break
            
            improved_steps = []
        
        print("\n=== Final Analysis Results ===")
        print(f"Total iterations needed: {iteration + 1}")
        print(f"Final convergence history: {self.convergence_history}")
        print("\nFinal solution:")
        print(current_solution)
        
        return {
            'final_solution': current_solution,
            'step_history': quantum_states,
            'final_steps': current_steps,
            'convergence_history': self.convergence_history,
            'iterations_needed': iteration + 1
        }

    def solve(self, problem: str, max_tokens: int = 2000) -> Dict:
        """
        Solve a mathematical problem using quantum-enhanced reflection.
        """
        print("\n=== Starting Mathematical Problem Analysis ===")
        print("\nProblem:", problem)
        print("Domain:", self.domain if self.domain else "General")
        
        # Initial solution generation
        full_prompt = f"{self.system_prompt}\n\nProblem to solve:\n{problem}"
        result = self.generate_with_reflection(full_prompt, max_tokens)
        
        # Analysis summary
        analysis = {
            'problem': problem,
            'solution': result['final_solution'],
            'steps': result['final_steps'],
            'convergence': result['convergence_history'],
            'iterations': result['iterations_needed'],
            'domain': self.domain,
            'complexity_scores': [self.analyze_step_complexity(step) for step in result['final_steps']]
        }
        
        print("\n=== Final Solution Analysis ===")
        print("\nProblem:", problem)
        print("\nDomain:", self.domain if self.domain else "General")
        print("\nComplexity Analysis:")
        for i, score in enumerate(analysis['complexity_scores'], 1):
            print(f"Step {i} Complexity: {score:.3f}")
        print(f"\nFinal Convergence Score: {analysis['convergence'][-1] if analysis['convergence'] else 'N/A'}")
        print(f"Total Iterations: {analysis['iterations']}")
        
        return analysis 
    def apply_quantum_operation(self, text: str) -> np.ndarray:
        """Apply quantum operations to analyze solution quality."""
        tokens = self.tokenizer.encode(text)
        features = np.zeros(self.dimension, dtype=complex)
        
        for i, token in enumerate(tokens[:self.dimension]):
            amplitude = token / self.tokenizer.vocab_size
            phase = np.exp(2j * np.pi * (i / self.dimension))
            features[i % self.dimension] = amplitude * phase
            
        features = features / np.linalg.norm(features)
        
        H = self.create_hamiltonian()
        U = expm(-1j * H)
        evolved_state = U @ features
        
        return evolved_state

    def create_hamiltonian(self) -> np.ndarray:
        """Create the Hamiltonian operator for quantum evolution."""
        H = np.zeros((self.dimension, self.dimension), dtype=complex)
        for i in range(self.dimension):
            for j in range(self.dimension):
                if i != j:
                    distance = min(abs(i - j), self.dimension - abs(i - j))
                    coupling = 1.0 / (1.0 + distance)
                    H[i, j] = coupling * np.exp(1j * np.pi * distance / self.dimension)
        H = (H + H.conj().T) / 2
        return H

    def measure_convergence(self, prev_state: np.ndarray, current_state: np.ndarray) -> float:
        """Measure the convergence between quantum states."""
        fidelity = np.abs(np.vdot(prev_state, current_state)) ** 2
        return float(fidelity)

def main():
    # Example usage with detailed output
    solver = GeneralQuantumSolver(domain="algebra")
    
    problem = """
  Determine all real numbers   $\alpha$ such that, for every positive integer $n$, the integer
\[\lfloor \alpha \rfloor + \lfloor 2\alpha \rfloor + \dots +\lfloor n\alpha \rfloor\]
is a multiple of $n$. (Note that $\lfloor z \rfloor$ denotes the greatest integer less than or equal to $z$. For example, $\lfloor -\pi \rfloor = -4$ and $\lfloor 2 \rfloor = \lfloor 2.9 \rfloor = 2$.)
check for even and odd integer numbers and get answer?
    """
    
    print("\n=== Testing General Quantum Solver ===")
    print("Initialized solver with domain:", solver.domain)
    print("Problem to solve:", problem)
    
    result = solver.solve(problem)
    
    print("\n=== Detailed Solution Summary ===")
    print("\nFinal Solution:")
    print(result['solution'])
    
    print("\nStep-by-Step Analysis:")
    for i, (step, complexity) in enumerate(zip(result['steps'], result['complexity_scores'])):
        print(f"\nStep {i+1}:")
        print("Complexity Score:", complexity)
        print("Content:", step)
    
    print("\nConvergence History:")
    for i, conv in enumerate(result['convergence'], 1):
        print(f"Iteration {i}: {conv:.4f}")
    
    print(f"\nTotal Iterations Required: {result['iterations']}")

if __name__ == "__main__":
    main()