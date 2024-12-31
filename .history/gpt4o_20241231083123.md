We are tasked with finding all real numbers \(\alpha\) such that for every positive integer \(n\), the sum 

\[
S_n = \lfloor \alpha \rfloor + \lfloor 2\alpha \rfloor + \cdots + \lfloor n\alpha \rfloor
\]

is a multiple of \(n\).

---

### Step 1: Express \(S_n\)
Using the properties of the floor function, for any real number \(\alpha\), we can write:
\[
\lfloor k\alpha \rfloor = k\alpha - \{k\alpha\},
\]
where \(\{x\} = x - \lfloor x \rfloor\) is the fractional part of \(x\).

Thus,
\[
S_n = \lfloor \alpha \rfloor + \lfloor 2\alpha \rfloor + \cdots + \lfloor n\alpha \rfloor
= (\alpha + 2\alpha + \cdots + n\alpha) - (\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\}).
\]
The sum of the first \(n\) terms of the arithmetic series \(\alpha, 2\alpha, \ldots, n\alpha\) is:
\[
\alpha + 2\alpha + \cdots + n\alpha = \alpha \cdot (1 + 2 + \cdots + n) = \alpha \cdot \frac{n(n+1)}{2}.
\]
Hence,
\[
S_n = \alpha \cdot \frac{n(n+1)}{2} - (\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\}).
\]

---

### Step 2: Condition for \(S_n\) to be a multiple of \(n\)
We require \(S_n \mod n = 0\). Substituting \(S_n\),
\[
\alpha \cdot \frac{n(n+1)}{2} - (\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\}) \equiv 0 \pmod{n}.
\]

#### Simplifying modulo \(n\):
1. Note that \(\frac{n(n+1)}{2} \mod n \equiv 0 \pmod{n}\), since \(\frac{n(n+1)}{2}\) is divisible by \(n\).
2. Therefore, the condition reduces to:
\[
-(\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\}) \equiv 0 \pmod{n}.
\]
Equivalently,
\[
\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\} \equiv 0 \pmod{n}.
\]

---

### Step 3: Analyze \(\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\}\)
The fractional parts \(\{k\alpha\}\) satisfy \(0 \leq \{k\alpha\} < 1\). For \(S_n\) to satisfy the modularity condition for all \(n\), this imposes significant constraints on \(\alpha\). 

#### Case 1: \(\alpha\) is an integer
If \(\alpha = m \in \mathbb{Z}\), then \(\lfloor k\alpha \rfloor = k\alpha = km\), so:
\[
S_n = m(1 + 2 + \cdots + n) = m \cdot \frac{n(n+1)}{2}.
\]
Since \(m \cdot \frac{n(n+1)}{2}\) is always a multiple of \(n\), the condition is satisfied for all \(n\). Hence, all integers \(\alpha\) work.

#### Case 2: \(\alpha\) is not an integer
If \(\alpha \not\in \mathbb{Z}\), then \(\{\alpha\} \neq 0\). The terms \(\{k\alpha\}\) will generally vary with \(k\), making their sum \(\{\alpha\} + \{2\alpha\} + \cdots + \{n\alpha\}\) unlikely to be divisible by \(n\) for all \(n\). For example, if \(\alpha = p/q\) (rational, not an integer), then \(\{k\alpha\}\) exhibits periodic behavior, and the modularity condition fails for sufficiently large \(n\).

---

### Step 4: Conclusion
The only values of \(\alpha\) that satisfy the condition for all \(n\) are integers. Thus, the solution is:
\[
\boxed{\alpha \in \mathbb{Z}}
\]