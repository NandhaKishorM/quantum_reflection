import numpy as np
from transformers import AutoTokenizer, LlamaForCausalLM
import torch
from scipy.linalg import expm
from typing import List, Tuple, Dict
import nltk
from nltk.tokenize import sent_tokenize
import re
nltk.download('punkt')

class QuantumReflectionSystem:
    def __init__(self, model_path: str = "unsloth/Meta-Llama-3.1-8B-Instruct", dimension: int = 512):
        self.dimension = dimension
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model components
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        self.model = LlamaForCausalLM.from_pretrained(model_path, device_map="auto")
        
        # Quantum components
        self.quantum_state = np.zeros(dimension, dtype=complex)
        
        # Enhanced convergence parameters
        self.max_iterations = 5  
        self.convergence_threshold = 0.98
        self.stability_window = 3
        self.stability_threshold = 0.001
        
        # Track solution history
        self.solution_history = []
        self.convergence_history = []
        
        # Solution found flag
        self.solution_found = False
        
        # Mathematical system prompt
        self.system_prompt = """You are a precise mathematical problem solver with expertise in various mathematical domains. When solving problems:

1. Break down the solution into clearly numbered steps
2. Format each step as: 
   Step N: [Brief title]
   [Detailed mathematical work]
   ∴ [Conclusion of this step]
3. Use rigorous mathematical notation
4. Justify each significant step
5. Highlight key insights with '→ Insight:'
6. End with a clear final answer

For each step:
- Show all work clearly
- Explain why the step is needed
- Note any assumptions made
- Highlight potential pitfalls
Important to remember just use abstract and symbolic reasoning nothing more nothing less.
"""

    def check_solution_stability(self, current_solution: str) -> bool:
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
            # Also check for "alpha = X" pattern where X is an integer
            alpha_values = set(re.findall(r'alpha\s*=\s*(\d+)', sol.lower()))
            return numbers.union(math_terms).union(alpha_values)
            
        solution_elements = [extract_key_elements(sol) for sol in recent_solutions]
        
        # Check if alpha value is consistently present
        alpha_found = all('alpha' in sol.lower() and '=' in sol for sol in recent_solutions)
        
        # Additional check for conclusive alpha value
        if alpha_found:
            alpha_values = []
            for sol in recent_solutions:
                matches = re.findall(r'alpha\s*=\s*(\d+)', sol.lower())
                if matches:
                    alpha_values.append(matches[0])
            if len(set(alpha_values)) == 1:  # Same alpha value in consecutive solutions
                self.solution_found = True
                print(f"\n=== Found consistent alpha value: {alpha_values[0]} ===")
        
        # Check if solutions have stabilized
        is_stable = all(
            len(solution_elements[i].symmetric_difference(solution_elements[i-1])) / 
            max(len(solution_elements[i]), 1) < self.stability_threshold
            for i in range(1, len(solution_elements))
        )
        
        # Remove oldest solution if window is full
        if len(self.solution_history) > self.stability_window:
            self.solution_history.pop(0)
            
        return is_stable and alpha_found

    def extract_solution_steps(self, response: str) -> List[str]:
        """Extract individual solution steps from the response."""
        steps = re.split(r'Step \d+[:.]\s+', response)[1:]
        return [step.strip() for step in steps]

    def create_step_reflection_prompt(self, step: str, step_number: int, total_steps: int, 
                                    quantum_state: np.ndarray) -> str:
        """Create a reflection prompt for a specific solution step."""
        return f"""
        {self.system_prompt}

        Please analyze and improve this Step {step_number} of {total_steps} in a mathematical solution:

        Current Step:
        {step}

        Consider:
        1. Is the mathematical reasoning in this step complete?
        2. Are all calculations correct and clearly shown?
        3. Are any important cases or conditions missing?
        4. Could the explanation be more precise?
        5. Is this step necessary for the solution?
        6. Does it connect logically to other steps?
        7. Does this step help determine the exact value of alpha?

        Quantum State Insight: Step certainty measure is {np.abs(quantum_state).mean():.2f}

        Provide an improved version of this specific step, maintaining the same step number and format:
        Step {step_number}: """

    def create_steps_integration_prompt(self, steps: List[str], quantum_state: np.ndarray) -> str:
        steps_text = "\n\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
        return f"""
        {self.system_prompt}

        Review these solution steps for logical flow and completeness:

        {steps_text}

        Consider:
        1. Do the steps flow logically?
        2. Are there any missing connections?
        3. Is the progression from each step to the next clear?
        4. Could any steps be combined or split?
        5. Is the final conclusion well-supported by the steps?
        6. Have we determined a specific integer value for alpha?

        Quantum State Insight: Solution coherence measure is {np.abs(quantum_state).mean():.2f}

        Provide an improved version with better integration between steps:
        """

    def generate_with_step_reflection(self, prompt: str, max_new_tokens: int = 2000) -> Dict:
        print("\n=== Starting Step-by-Step Mathematical Analysis ===")
        
        # Initial solution generation
        full_prompt = f"{self.system_prompt}\n\nProblem to solve:\n{prompt}"
        inputs = self.tokenizer.encode(full_prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                temperature=0.1,
                do_sample=True
            )
        
        initial_response = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=True)
        current_steps = self.extract_solution_steps(initial_response)
        
        print("\n=== Initial Solution Steps ===")
        print("Initial Response:", initial_response)
        print("\nExtracted Steps:")
        for i, step in enumerate(current_steps):
            print(f"\nStep {i+1}:")
            print(step)
        
        improved_steps = []
        quantum_states = []
        consecutive_stable_iterations = 0
        
        for iteration in range(self.max_iterations):
            print(f"\n=== Reflection Iteration {iteration + 1} ===")
            
            current_solution = " ".join(current_steps)
            print("\nCurrent Complete Solution:")
            print(current_solution)
            
            if self.check_solution_stability(current_solution):
                consecutive_stable_iterations += 1
                print(f"\nSolution stability detected! Consecutive stable iterations: {consecutive_stable_iterations}")
                if consecutive_stable_iterations >= self.stability_window:
                    print("\n=== Solution Stabilized ===")
                    break
            else:
                consecutive_stable_iterations = 0
                print("\nSolution not yet stable")
            
            if self.solution_found:
                print("\n=== Exact Solution Found ===")
                break
            
            for i, step in enumerate(current_steps):
                print(f"\nProcessing Step {i+1}:")
                print("Original step:", step)
                
                current_state = self.apply_quantum_operation(step)
                quantum_states.append(current_state)
                
                reflection_prompt = self.create_step_reflection_prompt(
                    step, i+1, len(current_steps), current_state
                )
                
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
                
                print("Improved step:", improved_step)
                
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

    def apply_quantum_operation(self, text: str) -> np.ndarray:
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
        fidelity = np.abs(np.vdot(prev_state, current_state)) ** 2
        return float(fidelity)

def main():
    system = QuantumReflectionSystem()
    
    prompt = '''
Determine all real numbers   $\alpha$ such that, for every positive integer $n$, the integer
\[\lfloor \alpha \rfloor + \lfloor 2\alpha \rfloor + \dots +\lfloor n\alpha \rfloor\]
is a multiple of $n$. (Note that $\lfloor z \rfloor$ denotes the greatest integer less than or equal to $z$. For example, $\lfloor -\pi \rfloor = -4$ and $\lfloor 2 \rfloor = \lfloor 2.9 \rfloor = 2$.)
check for even and odd numbers
    '''
    
    result = system.generate_with_step_reflection(prompt)
    
    print("\n=== Final Results Summary ===")
    print("\nFinal Solution:")
    print(result['final_solution'])
    
    print("\nIndividual Steps:")
    for i, step in enumerate(result['final_steps']):
        print(f"\nStep {i+1}:")
        print(step)
    
    print(f"\nTotal iterations required: {result['iterations_needed']}")
    print(f"Final convergence history: {result['convergence_history']}")

if __name__ == "__main__":
    main()