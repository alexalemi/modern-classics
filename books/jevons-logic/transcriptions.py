"""Hand transcriptions for Jevons's Elementary Lessons in Logic, read off the
page images of the base scan (elementarylesson00jevouoft), NOT the OCR.

Each entry replaces every OCR line whose centre falls in the band
(leaf, y0..y1) with the text given. Conventions (see assemble.py):

  - a paragraph whose lines open on TAB is set line for line (verse,
    displayed syllogisms, lists); if every line carries " | " it is a
    table; '""' is an empty cell;
  - any other paragraph is prose: the first one joins a sentence the
    page left open, the last one stays open for the next page;
  - \\( ... \\) and \\[ ... \\] are LaTeX (mathml.MATH);
  - an empty text drops the band (a table continued from the page
    before is given whole on the first page).

Jevons's letters: A E I O name the four propositions; X Y Z (italic in
the book) the major, middle and minor terms; A B C D with a b c d their
negatives in Lesson XXIII.
"""


def T(id, leaf, y0, y1, text, x0=None, x1=None):
    return dict(id=id, leaf=leaf, y0=y0, y1=y1, x0=x0, x1=x1, figure=False,
                text=text.strip("\n"))


TEXTS = [
    # --- Lesson V, p.39: the scheme of extension and intension
    T("t_extension", 57, 900, 1330, """
\tThe extension, extent, breadth, denotation, domain, sphere or application of a name consists of the individual things to which the name applies. | The intension, intent, depth, connotation, or implication of a name consists of the qualities the possession of which by those things is implied.
"""),
    # --- Lesson VII, p.58: (a + b)(a - b)
    T("t_algebra", 76, 1262, 1820, """
\\((a + b)(a - b) = a^2 - b^2\\);

which is readily seen to be true, as follows:

\\[\\begin{array}{r} a + b \\\\ a - b \\\\ \\hline a^2 + ab \\\\ -\\,ab - b^2 \\\\ \\hline a^2 + 0 - b^2. \\end{array}\\]
"""),
    # --- Lesson VIII, p.64: Aristotle's four kinds as to quantity
    T("t_quantity", 82, 2098, 2360, """
\tProposition:
\t    Universal.
\t    Particular.
\t    Singular.
\t    Indefinite.
"""),
    # --- Lesson IX, p.75: distribution of terms
    T("t_distribution", 95, 2284, 2600, """
\t"" | "" | Subject. | Predicate.
\tUniversal | Affirmative A. | Distributed. | Undistributed.
\tUniversal | Negative E. | Distributed. | Distributed.
\tParticular | Affirmative I. | Undistributed. | Undistributed.
\tParticular | Negative O. | Undistributed. | Distributed.
"""),
    # --- Lesson IX, p.79: truth of each from each
    T("t_truth", 99, 280, 690, """
\t"" | A is | E is | I is | O is
\tIf A be true | true | false | true | false.
\tIf E be true | false | true | false | true.
\tIf I be true | doubtful | false | true | doubtful.
\tIf O be true | false | doubtful | doubtful | true.
"""),
    # --- Lesson X, p.85: conversion by privative conception (bracketed pairs)
    T("t_privative", 105, 2008, 2550, """
\tA all metals are elements. | E no metals are compounds.
\tE no men are perfect. | A all men are imperfect.
\tI some men are trustworthy. | O some men are not untrustworthy.
\tO some men are not trustworthy. | I some men are untrustworthy.
"""),
    # --- Lesson XI, pp.94-95: the verse analysed in the diagrams
    T("t_burbidge", 114, 2170, 2600, """
\t"He who metes, as we should mete,
\tCould we His insight use, shall most approve,
\tNot that which fills most space in earthly eyes,
\tBut what—though Time scarce note it as he flies—
\tFills, like this little daisy at my feet,
\tIts function best of diligence in love."
"""),
    T("t_wordsworth", 115, 920, 1512, """
\t"Most sweet it is with unuplifted eyes
\t    To pace the ground, if path there be or none,
\tWhile a fair region round the traveller lies
\t    Which he forbears again to look upon;
\tPleased rather with some soft ideal scene,
\t    The work of fancy, or some happy tone
\tOf meditation slipping in between,
\t    The beauty coming, and the beauty gone."
\t                                        Wordsworth.
"""),
    # --- Lesson XIV, pp.124-125: the base scan of these two leaves is
    # blurred past reading (ABBYY returned noise); transcribed from the
    # 1893 witness, which prints the same plates, checked against the blur.
    T("t_dictum", 144, 0, 3100, """
Whatever is predicated of a term distributed whether affirmatively or negatively, may be predicated in like manner of everything contained under it.

Or more briefly:

What pertains to the higher class pertains also to the lower.

This merely means, in untechnical language, that what may be said of all the things of any sort or kind may be said of any one or any part of those things; and, secondly, what may be denied of all the things in a class may be denied of any one or any part of them. Whatever may be said of "All planets" may be said of Venus, the Earth, Jupiter, or any other planet; and, as they may all be said to revolve in elliptic orbits, it follows that this may be asserted of Venus, the Earth, Jupiter, or any other planet. Similarly, according to the negative part of the Dicta, we may deny that the planets are self-luminous, and knowing that Jupiter is a planet may deny that Jupiter is self-luminous. A little reflection would show that the affirmative Dictum is really the first of the Canons in a less complete and general form, and that the negative Dictum is similarly the second Canon. These Dicta in fact only apply to such cases of agreement between terms as consist in one being the name of a smaller class, and another of the larger class containing it. Logicians have for the most part strangely overlooked the important cases in which one term agrees with another to the extent of being identical with it; but this is a subject which we cannot fitly discuss here at any length. It is treated in my little work called The Substitution of Similars.

Footnote: Macmillan and Co. 1869.

Some logicians have held that in addition to the three laws which are called the Primary Laws of Thought,
"""),
    T("t_sufficient", 145, 0, 2300, """
there is a fourth called "The Principle or Law of Sufficient Reason." It was stated by Leibnitz in the following words:

Nothing happens without a reason why it should be so rather than otherwise. For instance, if there be a pair of scales in every respect exactly alike on each side and with exactly equal weights in each scale, it must remain motionless and in equilibrium, because there is no reason why one side should go down more than the other. It is certainly a fundamental assumption in mechanical science that if a body is acted upon by two perfectly equal forces in different directions it will move equally between them, because there is no reason why it should move more to one side than the other. Mr Mansel, Sir W. Hamilton and others consider however that this law has no place in logic, even if it can be held self-evident at all; and the question which appears open to doubt need not be discussed here.

I have so freely used the word axiom in this lesson that it is desirable to clear up its meaning as far as possible. Philosophers do not perfectly agree about its derivation or exact meaning, but it certainly comes from the verb ἀξιόω, which is rendered, to think worthy. It generally denotes a self-evident truth of so simple a character that it must be assumed to be true, and, as it cannot be proved by any simpler proposition, must itself be taken as the basis of reasoning. In mathematics it is clearly used in this sense.

See Hamilton's Lectures on Logic, Lectures 5 and 6.
"""),
    # --- Lesson XVI, p.136: some of the 64 combinations
    T("t_combinations", 158, 970, 1245, """
\tAAA | AEA | AIA | AOA | EAA | EEA
\tAAE | AEE | AIE | AOE | EAE | EEE
\tAAI | AEI | AII | AOI | EAI | EEI
\tAAO | AEO | AIO | AOO | EAO | &c.
"""),
    # --- Lesson XVI, p.137: the twelve moods that escape exclusion
    T("t_twelve", 159, 1895, 2305, """
\tAAA | EAE | IAI | OAO
\tAAI | EAO | (IEO) | ""
\tAEE | EIO | "" | ""
\tAEO | "" | "" | ""
\tAII | "" | "" | ""
\tAOO | "" | "" | ""
"""),
    # --- Lesson XVI, p.138: moods excluded, and the four figures
    T("t_excluded", 160, 405, 1170, """
\tExcluded by | "" | Number of moods.
\tNegative premises, | Rule 5 | 16
\tParticular premises | Rule 7 | 12
\tOne negative premise | Rule 6 | 12
\tOne premise particular | Rule 8 | 8
\tNegative conclusion | Rule 6 | 4
\tIllicit major | Rule 4 | 1
\tTotal excluded | "" | 53
\tValid moods | "" | 11
\tTotal | "" | 64
"""),
    T("t_figures", 160, 2060, 2600, """
\tX to denote the major term
\tY to denote the middle term
\tZ to denote the minor term

\t"" | 1st Fig. | 2nd Fig. | 3rd Fig. | 4th Fig.
\tMajor Premise | Y X | X Y | Y X | X Y
\tMinor Premise | Z Y | Z Y | Y Z | Y Z
\tConclusion | Z X | Z X | Z X | Z X
"""),
    # --- Lesson XVI, p.139: AEE in the first three figures
    T("t_aee1", 161, 1280, 1480, """
\tAll Y's are X's,
\tNo Z's are Y's;
\tTherefore no Z's are X's.
"""),
    T("t_aee2", 161, 1795, 1995, """
\tAll X's are Y's,
\tNo Z's are Y's;
\tTherefore no Z's are X's.
"""),
    T("t_aee3", 161, 2115, 2315, """
\tAll Y's are X's,
\tNo Y's are Z's,
\tNo Z's are X's,
"""),
    # --- Lesson XVI, p.140: the valid moods
    T("t_valid", 162, 405, 1105, """
\tValid Moods of the Syllogism.

\tFirst Figure. | Second Figure. | Third Figure. | Fourth Figure.
\tAAA | EAE | AAI | AAI
\tEAE | AEE | IAI | AEE
\tAII | EIO | AII | IAI
\tEIO | AOO | EAO | EAO
\t"" | "" | OAO | EIO
\t[AAI] | [EAO] | EIO | ""
\t[EAO] | [AEO] | "" | [AEO]
"""),
    # --- Lesson XVI, pp.141-142: the four moods of the second figure
    T("t_second1", 163, 2205, 2510, """
\tEAE | AEE
\tno X's are Y's, | all X's are Y's,
\tall Z's are Y's; | no Z's are Y's;
\t∴ no Z's are X's. | ∴ no Z's are X's.
"""),
    T("t_second2", 164, 236, 510, """
\tEIO | AOO
\tno X's are Y's, | all X's are Y's,
\tsome Z's are Y's; | some Z's are not Y's;
\t∴ some Z's are not X's. | ∴ some Z's are not X's.
"""),
    # --- Lesson XVII, p.145: the mnemonic verses
    T("t_barbara", 167, 578, 922, """
\tBarbara, Celarent, Darii, Ferioque, prioris;
\tCesare, Camestres, Festino, Baroko, secundæ;
\tTertia, Darapti, Disamis, Datisi, Felapton,
\tBokardo, Ferison, habet; Quarta insuper addit
\tBramantip, Camenes, Dimaris, Fesapo, Fresison.
"""),
    # --- Lesson XVII, p.148: Baroko and Bokardo
    T("t_baroko", 170, 1245, 1445, """
\tAll X's are Y's,
\tSome Z's are not Y's;
\tTherefore some Z's are not X's.
"""),
    T("t_baroko2", 170, 1697, 1910, """
\tAll not-Y's are not X's,
\tSome Z's are not-Y's;
\tTherefore some Z's are not X's.
"""),
    T("t_bokardo", 170, 2388, 2600, """
\tSome Y's are not X's,
\tAll Y's are Z's;
\tTherefore some Z's are not X's.
"""),
    # --- p.149
    T("t_bokardo2", 171, 400, 600, """
\tAll Y's are Z's,
\tSome not-X's are Y's;
\tTherefore some not-X's are Z's.
"""),
    T("t_indirect1", 171, 2423, 2600, """
\tAll X's are Y's (1)
\tSome Z's are not Y's (2)
\tTherefore some Z's are not X's (3)
"""),
    # --- p.150
    T("t_indirect2", 172, 530, 745, """
\tAll X's are Y's (1)
\tAll Z's are X's, contradictory of (3)
\tHence all Z's are Y's.
"""),
    T("t_indirect3", 172, 1175, 1385, """
\tSome Y's are not X's (1)
\tAll Y's are Z's (2)
\tTherefore some Z's are not X's (3)
"""),
    T("t_indirect4", 172, 1555, 1755, """
\tAll Z's are X's, contradictory of (3)
\tAll Y's are Z's (2)
\tHence all Y's are X's.
"""),
    # --- Lesson XVIII, p.155: prosyllogism and episyllogism
    T("t_episyllogism", 177, 1615, 1945, """
\tAll B's are A's,
\tAnd all C's are B's;
\tTherefore all C's are A's.
\tBut all D's are C's;
\tTherefore all D's are A's.
"""),
    # --- p.156: epicheirema, sorites
    T("t_epicheirema", 178, 225, 450, """
\tAll B's are A's, for they are P's,
\tAnd all C's are B's, for they are Q's;
\tTherefore all C's are A's,
"""),
    T("t_sorites", 178, 910, 1255, """
\tAll A's are B's,
\tAll B's are C's,
\tAll C's are D's,
\tAll D's are E's;
\tTherefore all A's are E's.
"""),
    T("t_sorites2", 178, 1685, 1960, """
\tFirst Syllogism. | Second Syllogism. | Last Syllogism.
\tB's are C's, | C's are D's, | D's are E's,
\tA's are B's; | A's are C's; | A's are D's;
\t∴ A's are C's. | ∴ A's are D's. | ∴ A's are E's.
"""),
    # --- Lesson XIX, p.161
    T("t_ponens", 183, 1745, 1960, """
\tIf A is B, C is D;
\tBut A is B;
\tTherefore C is D,
"""),
    T("t_tollens", 183, 2375, 2605, """
\tIf A is B, C is D;
\tBut C is not D;
\tTherefore A is not B.
"""),
    # --- p.162
    T("t_affirming", 184, 1005, 1232, """
\tIf A is B, C is D;
\tBut C is D;
\tTherefore A is B,
"""),
    T("t_denying", 184, 2362, 2590, """
\tIf A is B, C is D;
\tBut A is not B;
\tTherefore C is not D.
"""),
    # --- p.166: disjunctive syllogism
    T("t_disj1", 188, 650, 850, """
\tA is either B or C,
\tBut A is B;
\tTherefore A is not C.
"""),
    T("t_disj2", 188, 2005, 2220, """
\tA is either B or C,
\tBut A is not B;
\tTherefore A is C.
"""),
    # --- p.167: dilemmas
    T("t_dilemma1", 189, 1375, 1590, """
\tIf A is B, C is D; and if E is F, C is D;
\tBut either A is B, or E is F;
\tTherefore C is D.
"""),
    T("t_dilemma2", 189, 2172, 2378, """
\tIf A is B, C is D; and if E is F, G is H;
\tBut either A is B, or E is F;
\tTherefore either C is D, or G is H.
"""),
    # --- p.168
    T("t_dilemma3", 190, 1090, 1305, """
\tIf A is B, C is D; and if E is F, G is H;
\tBut either C is not D, or G is not H;
\tTherefore either A is not B, or E is not F.
"""),
    # --- Lesson XXI, p.179: petitio principii
    T("t_petitio1", 201, 1888, 2100, """
\tB is C,
\tA is B,
\ttherefore A is C,
"""),
    T("t_petitio2", 201, 2375, 2578, """
\tC is B,
\tA is C,
\ttherefore A is B,
"""),
    # --- Lesson XXII, p.186: the eight propositions
    T("t_eight", 208, 1620, 2160, """
\tU | All X is all Y. | Affirmative.
\tI | Some X is some Y. | Affirmative.
\tA | All X is some Y. | Affirmative.
\tY | Some X is all Y. | Affirmative.
\tE | No X is (any) Y. | Negative.
\tω | Some X is not some Y. | Negative.
\tη | No X is some Y. | Negative.
\tO | Some X is no Y. | Negative.
"""),
    # --- Lesson XXII, p.188: Thomson's table of moods (eight propositions;
    # each negative cell holds two moods, set here as "X / Y")
    T("t_thomson", 210, 282, 2350, """
\tTable of Moods of the Syllogism.

\t"" | First Figure, Affirm. | First Figure, Neg. | Second Fig., Affirm. | Second Fig., Neg. | Third Figure, Affirm. | Third Figure, Neg.
\ti | UUU | EUE / UEE | UUU | EUE / UEE | UUU | EUE / UEE
\tii | AYI | ηYω / AOω | YYI | OYω / YOω | AAI | ηAω / Aηω
\tiii | AAA | ηAη / Aηη | YAA | OAη / Yηη | AYA | ηYη / AOη
\tiv | YYY | OYO / YOO | AYY | ηYO / AOO | YAY | OAO / YηO
\tv | AII | ηIω / Aωω | YII | OIω / Yωω | AII | ηIω / Aωω
\tvi | IYI | ωYω / IOω | IYI | ωYω / IOω | IAI | ωAω / Iηω
\tvii | UYY | EYO / UOO | UYY | EYO / UOO | UAY | EAO / UηO
\tviii | AUA | ηUη / AEη | YUA | OUη / YEη | AUA | ηUη / AEη
\tix | UAA | EAE / Uηη | UAA | EAE / Uηη | UYA | EYE / UOη
\tx | YUY | OUO / YEE | AUY | ηUO / AEE | YUY | OUO / YEE
\txi | UII | EIO / Uωω | UII | EIO / Uωω | UII | EIO / Uωω
\txii | IUI | ωUω / IEη | IUI | ωUω / IEη | IUI | ωUω / IEη
"""),
    # --- Lesson XXIII, p.196
    T("t_organic", 218, 222, 565, """
\tOrganic substance is either vegetable or animal.
\tVegetable substance consists mainly of carbon, hydrogen, and nitrogen.
\tAnimal substance consists mainly of carbon, hydrogen, and nitrogen.
"""),
    T("t_letters1", 218, 815, 1175, """
\tA = organic substance,
\tB = vegetable substance,
\tC = animal substance,
\tD = consisting mainly of carbon, hydrogen, and nitrogen,
"""),
    T("t_combos8", 218, 1315, 1600, """
\t(1) | ABCD | AbCD | (5)
\t(2) | ABCd | AbCd | (6)
\t(3) | ABcD | AbcD | (7)
\t(4) | ABcd | Abcd | (8)
"""),
    T("t_premises1", 218, 1695, 1900, """
\tA must be either B or C,
\tB must be D,
\tC must be D.
"""),
    T("t_remain1", 218, 2185, 2390, """
\tABCD
\tABcD
\tAbCD.
"""),
    # --- p.197
    T("t_letters2", 219, 1875, 2150, """
\tA = similar figure,
\tB = triangle,
\tC = having corresponding angles equal,
\tD = having corresponding sides proportional,
"""),
    T("t_identical1", 219, 2245, 2325, """
\tA is identical with CD,
"""),
    T("t_identical2", 219, 2375, 2460, """
\tBC is identical with BD;
"""),
    # --- p.198
    T("t_combos16", 219 + 1, 543, 1088, """
\tABCD | aBCD
\tABCd | aBCd
\tABcD | aBcD
\tABcd | aBcd
\tAbCD | abCD
\tAbCd | abCd
\tAbcD | abcD
\tAbcd | abcd
"""),
    T("t_remain2", 220, 1733, 2005, """
\tABCD | aBcd
\tAbCD | abCd
\t"" | abcD
\t"" | abcd
"""),
    # --- Lesson XXVI, pp.220-221: mathematical induction
    T("t_induction", 242, 270, 2650, """
squares of a and b. However often we try this it will be found true; thus if a = 10 and b = 7, the product of the sum and difference is 17 × 3 = 51; the squares of the quantities are 10 × 10 or 100 and 7 × 7 or 49, the difference of which is also 51. But however often we tried the rule no certainty would be added to it; because when proved algebraically there was no condition which restricted the result to any particular numbers, and a and b might consequently be any numbers whatever. This generality of algebraical reasoning by which a property is proved of infinite varieties of numbers at once, is one of the chief advantages of algebra over arithmetic. There is also in algebra a process called Mathematical Induction or Demonstrative Induction, which shows the powers of reasoning in a very conspicuous way. A good example is found in the following problem:—If we take the first two consecutive odd numbers, 1 and 3, and add them together the sum is 4, or exactly twice two; if we take three such numbers 1 + 3 + 5, the sum is 9 or exactly three times three; if we take four, namely 1 + 3 + 5 + 7 the sum is 16, or exactly four times four; or generally, if we take any given number of the series, 1 + 3 + 5 + 7 + ... the sum is equal to the number of the terms multiplied by itself. Anyone who knows a very little algebra can prove that this remarkable law is universally true, as follows—Let n be the number of terms, and assume for a moment that this law is true up to n terms, thus—

\\[1 + 3 + 5 + 7 + \\dots + (2n - 1) = n^2.\\]

Now add \\(2n + 1\\) to each side of the equation. It follows that—

\\[1 + 3 + 5 + 7 + \\dots + (2n - 1) + (2n + 1) = n^2 + 2n + 1.\\]

But the last quantity \\(n^2 + 2n + 1\\) is just equal to \\((n + 1)^2\\); so that if the law is true for n terms it is true also for n + 1 terms. We are enabled to argue from each single case of
"""),
    T("t_prime", 243, 1935, 2010, """
\\[x^2 + x + 41 = \\text{prime number.}\\]
"""),
    T("t_primes", 243, 2425, 2580, """
\t0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10
\t41 | 43 | 47 | 53 | 61 | 71 | 83 | 97 | 113 | 131 | 151
"""),
    # --- Lesson XXVIII, pp.246-247: Mill's methods in symbols
    T("t_agreement", 268, 1055, 1530, """
\tAntecedents. | Consequents.
\tABC | abc
\tADE | ade
\tAFG | afg
\tAHK | ahk
\t...... | ......
\t...... | ......
"""),
    T("t_difference", 268, 1815, 2015, """
\tAntecedents. | Consequents.
\tABC | abc
\tBC | bc
"""),
    T("t_joint", 269, 300, 1050, """
\tAntecedents. | Consequents.
\tABC | abc
\tADE | ade
\tAFG | afg
\tAHK | ahk
\t...... | ......
\tPQ | pq
\tRS | rs
\tTV | tv
\tXY | xy
\t...... | ......
"""),
    # --- Questions and Exercises
    T("t_q_terms3", 321, 1950, 2645, """
\tMetropolis | Consciousness | Sect
\tBook | Lord Chancellor | Nation
\tLibrary | Vegetable Kingdom | Institution
\tGreat Britain | Brilliance | Light
\tCæsar | Weight | Observation
\tVoid | Sensation | Tongue
\tGold | Cæsar | Air
\tPrime Minister | Cæsarism | Mentor
\tIndigestibility | Application | Anarchy
\tManchester | Individual | Retribution
\tRecollection | Volume | Solemnity
\tInsignificant | Language | Understanding
\tBrilliant | Adornment | Geology
\tIndependence | Agreement | Demeanour
\tHeaviness | Obliquity | Resemblance
\tIllustration | Motionless | Departure
\tSection | Henry VIII. | Nestor
\tWhiteness | Formal Logic | Alexander
"""),
    T("t_q_terms3b", 322, 265, 705, ""),
    T("t_q_terms4", 322, 1660, 2220, """
\tBill | Minister | Subject | Letter
\tTable | Clerk | Object | Star
\tTerm | Order | Earth | Pole
\tSchool | Wood | Law | Reason
\tAir | Bull | Sensation | Bed
\tGlass | Volume | Art | Bowl
\tPeer | Scale | Interest | End
\tSense | Feeling | Paper | Division
\tBall | Kind | Bolt | Class
"""),
    T("t_q_terms5", 323, 1805, 2305, """
\tEmperor | Animal | Planet
\tTeacher | Dissenter | Mammalian
\tBaptist | Individual | Matter
\tTimber | Jupiter | Solicitor
\tPerson | Ruler | Quadruped
\tHorse | Organized substance | Being
\tHeavenly body | Lawyer | Napoleon III.
\tChristian | Alexander | Episcopalian
"""),
    T("t_q_division", 331, 1695, 2410, """
\t(1) People: Laity, Aliens, Naturalized Subjects, Peers, Natural-born Subjects, Clergy, Baronets, Commons.
\t(2) Triangle: Equiangular, Isosceles, Right-angled, Scalene, Obtuse-angled.
\t(3) Reasoning: Induction (Imperfect), Deduction, Mediate Inference, Induction, Hypothetical Syllogism, Disjunctive Syllogism.
"""),
    T("t_q_antecedents", 352, 2090, 2625, """
\tAntecedents. | Consequents.
\tABDE | stqp
\tBCD | qsr
\tBFG | vqu
\tADE | tsp
\tBHK | zqw
\tABFG | pquv
\tABE | pqt
"""),
]
