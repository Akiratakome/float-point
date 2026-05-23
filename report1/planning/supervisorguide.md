Dear Yudong,

I have looked only at your second draft, so I haven't made a comparison with the first one. If you think that some of my comments are resolved by reverting to the first version, then perhaps that suggests the answer.

Unfortunately I have not had time to read your full report yet, only up to Section 5.5. I hope to come back to this later today or tomorrow. My apologies, but hopefully my suggestions so far will give you something to be working on.

Firstly, can I remind you of the rules around the use of AI/LLMs in your submitted work, as given on p25 of the Course Handbook:
https://mphil.csc.cam.ac.uk/wp-content/uploads/2025/10/SciComp_Mphil_Handbook-2025-26.pdf
In Draft 2, the current text in the Word Count Declaration and Abstract is clearly a directive to an LLM.

Beyond that; there is a lot of good material in the report and you have clearly done a lot of careful and impressive work. However, the layout and explanations need to be clearer. There are some terms that you do not define for non-specialists, and in particular I found your frequent mention of “rows” confusing. This suggests it relates to a single table somewhere rather than multiple one tables.
Some of this will be helped by adding code-examples to explain the STRICT_IEEE macros (or enums?). Extra interpretation of your tables will also help (rather than simply repeating the numbers).

More detailed comments are below; if you need any clarification, let me know.

Kind regards,

Philip

Chapter 1:
You should give some background about why we want to solve the compressible Euler equations, e.g. giving some applications, and the requirements for simulations to run quickly but accurately enough to compare to experiment. This will also relate to how precise the result needs to be.

You should give some background and existing work for finite-precision and mixed-precision use in CFD solutions. Identify some papers/codes where this has been done and give a brief summary of them, and any limitations of existing work.

I also suggest you mention CUDA/GPUs and give some background on these. Mention the different precisions and their differing performances, even between cards of the same vintage (e.g. the enterprise Ampere range against the consumer RTX 3000 range).

CHapter 2
Section 2.1: What is \gamma? How are p and E related?
Section 2.2: Give the ideal-MHD equations. You have described them in words; giving equations is far more precise. What does the div B = 0 constraint mean, and why do we care about preserving it?

Parts of Section 2.3 feel a bit unnecessary; I think it simply summarises what is in Chapter 3. Either it should refer purely to background literature or parts of this can be moved into later sections. E.g. “Toro’s stronger shock-tube cases then test the same code path
under larger pressure and velocity jumps” is better placed near the actual test-descriptions themselves.
You should also be careful that you do not assume knowledge of terms before using them. E.g. you have referred to HLLC before defining it (or referencing it).

Section 2.4: You should mention the exponent ranges as well as the significand. Also, define your terms; what is “unit roundoff” for example?
Expand on what “practical design question”; what is the question, what options are there and what solutions are generally proposed? The reference you have is for linear algebra, so don’t discuss anything linear algebra specific, but mention anything that might relate to HRSC.
Associativity can be more of a problem than just the last few digits. Consider (1e-18 + 1)-1 versus 1e-18 + (1-1). Relate -Ofast to -O3 where in the latter case, reordering is not allowed. Other operations such as 1/x, sqrt(x) and similar are also affected.

CHapter 3
Section 3.1: Define the CFL constraint [ I now see it in Section 3.4; some reordering may be necessary. ]
Number all your equations; not just the ones you refer to in the text. This will help your assessors navigate your report.
Section 3.2: Why is slope-limiting needed? [ I now see this in Section 3.4; again, reordering may be necessary. ]

Section 3.3: “vertical” is redundant.
Who is Davis? The “Davis-style” should be referenced.
Page 11: Your first equation has < only. Your second equation has <= everywhere, so that some answers are either multiply defined or undefined.
Section 3.4: “max_ij max(v_x,ij, v_y,ij) <= C_CFL is not equivalent to the previous equation.
What is TVD?

Section 3.5: “well resolved in binary64 can lose accuracy in binary32” - I suggest “sufficiently accurate in binary64, but insufficiently so in binary32”. There is already a loss of accuracy in binary64 relative to exact arithmetic, so “well resolved” feels inaccurate.
P13: The accuracy of FMA also depends on hardware; I believe CPUs have a more accurate intermediate calculation versus GPUs that stay with the same precision throughout.

What is “RIEMANN_STRICT_INEQUALITY”? Presumably this is your own code-construct, in which case explain it, giving code examples as appropriate. Similarly for STRICT_IEEE and FAST_MATH.

Table 3.1 is very useful as a summary. I suggest increasing the spacing between rows; otherwise they almost merge into each other, especially when reading along rows.

Section 3.6: You should expand on this to the same detail as for Euler. I.e. define the wave-speeds, describe the divergence cleaning extra equation.

Chapter 4:

Reduction ordering for CFL shouldn’t be affected by finite-precision. That would only apply for a sum, not for a minimum/maximum.

Section 4.1:
What is AMReX? (In fact, as you don’t use it, you don’t actually need to mention it.)
Give code-examples of how FLOAT_PRECISION is used in practice.
Reference “Boost::Multiprecision”.
“Device evidence uses a disclosed toolchain split:” What does this mean? Also, why did you run some tests on WSL and some with Windows build-tools? You need to use the same compiler for all tests, given the likely effect of different optimizations.

Section 4.2:
Although the assessors will have access to your source-code, you shouldn’t refer them directly to that in the report. Instead you should either summarize their function or give code-snippets as appropriate. Some implementation details, such as section 4.1: “JSON and Markdown rows that feed the chapter tables” are irrelevant to the academic content of the report.

What is CUDA; what are thread-blocks; what are “OpenMP schedules”? More importantly, you have not mentioned Verificarlo before. This should be in Chapter 1 (as well as Raptor), giving a brief overview of its capabilities. In particular, describe MCA and what it does.

Section 4.3: What do you mean by “matched device evidence”? You should also explain the meaning of compiler flags -ffp-contract=off etc.
This section feels wordy, and better expressed either by equations (for MCA etc.) or by just showing tables/axes instead of describing what you are going to show later.

Section 4.4: What is SSIM?
You define R_ref, but what does it mean? E.g. if this is very small or very large, what will it tell us?
Table 4.1: Again, add more spacing (and perhaps lines) between rows.
Either here or in Chapter 5 you need to give the initial conditions for the Toro and LW tests.
You keep referring to “rows” (e.g. CPU/GPU rows) but the reader/assessor has not yet seen an example of what this means so cannot visualise/understand the full context for this yet. Either find another way of referring to the “rows” or give a toy/initial example early on, and describe what that shows before moving on to fuller cases in a later section.


Also, how do you translate the N=800 fp64 reference into lower-resolution results for comparison? Is this by cell-averaging, taking specific point values, or something else?

Chapter 5:
“Chapter 4 is the owner of …” is very unusual phrasing.

Section 5.2: Table 5.1 is good (although slightly unclear what variable L_1 is based on). However, the paragraph before that largely repeats the numbers in the table without interpreting them relative to what you are testing for.
Figs 5.1-5.3 should be larger. Put the resolution and output times in the caption not as figure titles. Also mention what solver and Riemann solver you are using.

Section 5.3: Again, Table 5.2 is good (although do you need 6 decimal places; 3 or 4 may be sufficient and make it clearer), but the main text mostly repeats the numbers in that table. You need to explain what the results mean, e.g. the relative sizes of them, etc.
Figs 5.4 and 5.5: Schlieren plots are better in black-and-white, so the assessors can compare with the literature. Again, what Riemann solver?

Section 5.4: Again, more interpretation of the results is needed. How does the LW12 density difference in the top right relate to the waves present there, and what does this tell you about the effect of finite-precision arithmetic on the parts of the algorithm that those waves indicate (e.g. do they trigger particular HLLC branches)?

Figure 5.7 is rather washed-out; make the colour scheme clearer.

Tables 5.3 and 5.4: As all the numbers are zeros, I’m not sure what setting this out in tables tells us. At the top of p28 you then spend several sentences describing that there is no difference between CPU and GPU. This can be described more succinctly.

Section 5.6: You mention an L_1 and L_\infty range. Here I would like to see more detail of the actual values for the different tests.

FIgure 5.8: These plots need to be larger.

** I only reached page 28; I will return to this later. **

References:
Careful with capitalization; e.g. “hll” versus “HLL”. In BibTeX you fix this by writing {HLL} instead of HLL.


I have now had time to finish reading your report; my further comments are below.
Overall I know you have done a lot of good work, and Chapter 6 summarises your conclusions well. However, some of the explanations need to be more logically laid out.

Kind regards,

Philip

-----

Table 5.5 is a little confusing due to specifying the ranges (because you don’t specify which of the tests the different values correspond to). However, the way you have presented Table 5.6 is a lot clearer to me. Consider restricting Table 5.5 to just the values for a specific test-case (probably the one that gives the most change, if that’s possible). It might also be inappropriate to mix 1D and 2D solutions as they may demonstrate different behaviours.

Fig 5.8 the plots are too small; make them at least double the size. You could plot density alone as the same features are visible in both density and pressure.

The compiler-flags are a little difficult to read as part of a sentence. I suggest you present them in the same way as code-snippets (see https://www.overleaf.com/learn/latex/Code_listing).

Figure 5.9 is good and makes it clear that none of the solvers diverge very rapidly over their run-time; however I don’t think giving the calculated best-fit slopes in Table 5.7 adds anything. The right-hand labels in FIg 5.9 are a little small, and I can only see 10 lines on the plot but 22 labels. Presumably some overlap exactly, but you need to make this clear.

P31: Do you know why the solver did not complete in 600s? You should be able to see what the dt value does, or plot intermediate output results to see its behaviour. The Toro-123 test is definitely sensitive, but there are usually possible tweaks to avoid instabilities (as I suspect is happening). Highlighting that that test is sensitive to simply changing <= to < is definitely interesting.

Chapter 6:
Section 6.1 is a good summary of how you have decided on your analysis approach.
Section 6.2: How is p32 different from fp32? This may be relevant to mention when you describe Verificarlo in Chapter 1 or 2. Apart from that, this is a good summary.
Sections 6.3 and 6.4 are similarly good summaries of the work you have done and you intended next steps.

Chapter 7: I think this repeats what you said in Chapter 6, in a much less clear way. I suggest removing Chapter 7 entirely, unless I have missed something that makes it different.


Dear all,

Thank you for sending me your reports. Hopefully my comments are clear; you have all been working hard and producing good and interesting results, so my comments are intended to help you make this clear to your assessors.

A few general points that I've mentioned to some of you:

When giving references, usually you should give the authors names:
“The Widget-solver, as proposed by MacMillan, Dent, and Prefect [2], can be written as follows:”
unless you are writing a literature review:
"MHD simulations are used in the simulation of plasmas [42] and lightning strikes on aircraft [54]."
This is a little vague; see what reads best. It can help the assessors to know whose paper you are referencing for particular numerical methods, etc.

In references, simply putting “HLLC” usually renders as “hllc” in the bibliography. In the BibTex file, use “{HLLC}” instead to fix this.

You need to make sure that everything is ordered so that the assessors can read from start to finish without wondering what a particular term or word means.
Although the assessors will generally know HRSC schemes, Euler, MHD, and similar, they need to see some background on that so that they know that you know them as well! Some less common topics (i.e. those not covered in any of the CFD or HPC lectures) may need to be covered in more detail.

Make sure your plots are large enough with clear labels. Roughly; if I have to zoom in the PDF to read axis labels or plots, they are too small.

Let me know if you need any further assistance.

Kind regards,

Philip