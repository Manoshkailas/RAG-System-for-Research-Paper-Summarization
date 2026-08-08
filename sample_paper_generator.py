import os
import sys

def create_sample_pdf(output_path: str = "sample_paper.pdf"):
    """
    Creates a sample academic paper PDF or text file for quick testing.
    Uses pypdf / ReportLab if available, or plain text PDF structure fallback.
    """
    paper_content = """Attention Is All You Need (Academic Showcase Sample)
Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin

ABSTRACT
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. We propose the Transformer, a novel model architecture relying entirely on self-attention mechanisms to compute representations of its input and output without using sequence-aligned RNNs or convolution. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.

1. INTRODUCTION
Recurrent neural network models, particularly long short-term memory (LSTM) and gated recurrent (GRU) neural networks, have been firmly established as state of the art approaches in sequence modeling and language tasks. However, the sequential nature of RNNs precludes parallelization within training examples, which becomes critical at longer sequence lengths. In this work we propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output.

2. METHODOLOGY AND SYSTEM MODEL
The Transformer follows an encoder-decoder structure using stacked self-attention and point-wise, fully connected layers.
- Encoder: The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers: Multi-Head Self-Attention and Position-wise Feed-Forward Networks.
- Scaled Dot-Product Attention: Compute attention weights as Softmax(Q K^T / sqrt(d_k)) V.
- Multi-Head Attention: Allows the model to jointly attend to information from different representation subspaces at different positions.

3. RESULTS AND EXPERIMENTAL EVALUATION
On the WMT 2014 English-to-German translation task, the big Transformer model achieves a new state-of-the-art BLEU score of 28.4, outperforming existing best models by over 2.0 BLEU. Training took 3.5 days on 8 P100 GPUs, a fraction of the cost of traditional RNN architectures.

4. DISCUSSION AND LIMITATIONS
While the Transformer eliminates sequential recurrence, the quadratic computational complexity O(n^2) of full self-attention with respect to sequence length n presents memory bottlenecks for extremely long document contexts. Future work focuses on sparse attention patterns.

5. CONCLUSION
In this work, we presented the Transformer, the first sequence transduction model based entirely on attention, replacing traditional recurrent layers with multi-headed self-attention.
"""

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        y = height - 50

        lines = paper_content.split('\n')
        for line in lines:
            if y < 50:
                c.showPage()
                y = height - 50
            if line.isupper() or line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5."):
                c.setFont("Helvetica-Bold", 12)
            else:
                c.setFont("Helvetica", 10)

            # Simple word wrap
            words = line.split()
            current_line = ""
            for w in words:
                if len(current_line + " " + w) > 85:
                    c.drawString(50, y, current_line)
                    y -= 15
                    current_line = w
                else:
                    current_line += " " + w if current_line else w
            if current_line:
                c.drawString(50, y, current_line)
                y -= 15

        c.save()
        print(f"[OK] Created sample PDF paper at: {output_path}")

    except ImportError:
        # Fallback: create raw PDF stream manually or fallback text paper
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(paper_content)
        print(f"[OK] Created sample paper text/PDF file at: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "sample_paper.pdf"
    create_sample_pdf(out)
