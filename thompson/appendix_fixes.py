"""Restored mathematics for the appendices of Light Visible and Invisible.

Every displayed formula in these appendices is a two-dimensional object — a
built-up fraction, a subscript, a Greek delta — and the scanner flattens all
of it. Eighteen numbered formulas plus the notation table came through as
debris: "2 * r "", ") i ( ^", "j-, ~ i*. L_ rT?i". Several vanished outright,
leaving the prose to say "the formula becomes" and then say nothing.

They were read back off the page images (printed pp. 57-69, scan leaves
n80-n92 of lightvisibleinvi00thomrich) and are restored here as indented
display blocks, which assemble.py renders as <pre>.

This is the same class of damage as the wave-length table of appendix four,
and it has the same remedy: a table or a formula cannot be recovered from the
OCR by any rule, only transcribed from the page.

Each entry must still match, or prep.py stops — see SOURCE_FIXES for why.
"""

APPENDIX_FIXES = [

    # ---- Method of reckoning curvature, printed pp. 57-58 -------------
    ("an arc of length 8s, the direction changes by an amount 80, the "
     "curvature is 86/8s. But the angle BO = 8s /r, where r is the radius "
     "of curvature ; hence the curvature = BsfrSs = I \\r.",
     "an arc of length δs, the direction changes by an amount δθ, "
     "the curvature is δθ/δs. But the angle δθ = δs/r, "
     "where r is the radius of curvature; hence the curvature = "
     "δs/rδs = 1/r."),

    ("the construction that MA. MB = (PM)2;",
     "the construction that\n\n    MA . MB = (PM)²"),

    ("assuming PM as unity, But, for small apertures, AM is small compared "
     "with 2r, and may be neglected in the denominator, whence, to a first "
     "approximation, 2 * r \"",
     "assuming PM as unity,\n\n"
     "    MA = 1/MB = 1/(2r − AM)\n\n"
     "But, for small apertures, AM is small compared with 2r, and may be "
     "neglected in the denominator, whence, to a first approximation,\n\n"
     "    MA = ½ · 1/r"),

    ("the numerical factor ^ disappears", "the numerical factor ½ disappears"),

    # ---- Notation, printed p. 60 --------------------------------------
    ("""Equivalent in Current Notation.

Focal curvature, or Focal power oflens or mirror ( = dioptrics, if metre is taken as unit of length) .....

1 . J /

Curvature of Surface ....

Curvature of Incident wave ; i.e. curvature which ii has acquired by having travelled from point of origin (" incident focus ") to incidence ....

\\ , I "

Curvature of Resultant wave; i.e. curvature with which wave emerges from the lens ......

Velocity-constant of medium ; i.e. velocity of light in that medium compared with velocity in air taken as unity

) i ( ^""",
     """    Symbol   Meaning                                 Current
                                                     notation
    ---------------------------------------------------------
      F      Focal curvature, or focal power of a      1/f
             lens or mirror (= dioptries, if the
             metre is taken as the unit of length)
      R      Curvature of surface                      1/r
      U      Curvature of incident wave; that is,      1/u
             the curvature it has acquired by
             travelling from its point of origin
             (the "incident focus") to incidence
      V      Curvature of resultant wave; that is,     1/v
             the curvature with which the wave
             emerges from the lens
      h      Velocity-constant of the medium; that     1/μ
             is, the velocity of light in that
             medium compared with the velocity in
             air, taken as unity"""),

    # ---- Expansion of curvatures, printed p. 61 -----------------------
    ("the formula for the new curvature K being as follows : — »",
     "the formula for the new curvature R′ being as follows:\n\n"
     "    R′ = R · 1/(1 ± Rd)                         [1]"),
    # ---- Refraction formulae, printed pp. 62-65 -----------------------
    ("V=hU . . [2]", "    V = hU                                      [2]"),

    ("Hence in this case the formula is v=\\a ... [3]",
     "Hence in this case the formula is\n\n"
     "    V = (1/h)U                                 [3]"),

    ("F=R(i-h] . [4]", "    F = R(1 − h)                              [4]"),

    ("velocity-constants hl and //2, the formula becomes",
     "velocity-constants h₁ and h₂, the formula becomes\n\n"
     "    F = R (h₁ − h₂)/h₁                          [5]"),

    ("curvature (R) of the surface is given by the rule",
     "curvature (R) of the surface is given by the rule\n\n"
     "    F = R (h − 1)/h                             [6]"),

    ("As before, for any two media having respective velocityconstants kl "
     "and hy the formula becomes which, in the present case where //1</^9, "
     "will give F ot opposite sign to R.",
     "As before, for any two media having respective velocity-constants h₁ "
     "and h₂, the formula becomes\n\n"
     "    F = R (h₁ − h₂)/h₁                      [5 bis]\n\n"
     "which, in the present case where h₁ < h₂, will give F of opposite "
     "sign to R."),

    ("or, in symbols, For an emergent wave, possessing initial curvature U "
     "in the medium, the formula will be Or, for the case of a wave passing "
     "from a medium of velocity-constant hl to another of velocity-constant "
     "h^ the formula will be yJ^U+F . . [9]",
     "or, in symbols,\n\n"
     "    V₁ = hU + F₁                                [7]\n\n"
     "For an emergent wave, possessing initial curvature U in the medium, "
     "the formula will be\n\n"
     "    V₂ = (1/h)U + F₂                            [8]\n\n"
     "Or, for the case of a wave passing from a medium of velocity-constant "
     "h₁ to another of velocity-constant h₂, the formula will be\n\n"
     "    V = (h₂/h₁)U + F                            [9]"),

    # ---- Lens formulae, printed pp. 65-66 -----------------------------
    ("the plane wave will be This formula may be compared with that in the "
     "current notation, (p. 36), gives an illustration, in which however "
     "7?x is zero, as the first face of the lens is flat.",
     "the plane wave will be\n\n"
     "    F = (1/h)F₁ + F₂\n\n"
     "But\n\n"
     "    F₁ = R₁(1 − h),\n\n"
     "and\n\n"
     "    F₂ = − R₂ (1 − h)/h ;\n\n"
     "whence\n\n"
     "    F = R₁(1 − h)/h − R₂(1 − h)/h,\n\n"
     "or\n\n"
     "    F = (R₁ − R₂)(1 − h)/h                      [10]\n\n"
     "This formula may be compared with that in the current notation,\n\n"
     "    1/f = { 1/r₁ − 1/r₂ } (μ − 1).\n\n"
     "Fig. 20 (p. 36) gives an illustration, in which however R₁ is zero, "
     "as the first face of the lens is flat."),

    ("In the case of a lens composed of a medium 7/9, lying between two "
     "other media hl and hy the formula becomes",
     "In the case of a lens composed of a medium h₂, lying between two "
     "other media h₁ and h₃, the formula becomes\n\n"
     "    F = 1/(h₁h₂) { R₁(h₁ − h₂)h₂ + R₂(h₂ − h₃)h₁ }   [11]"),

    ("The latter factor, 1—r~) or /x - i, is a mere numeric",
     "The latter factor, (1 − h)/h, or μ − 1, is a mere numeric"),

    ("at end of § 4 above at once gives j-, ~ i*. L_ rT?i",
     "at end of § 4 above at once gives\n\n"
     "    F = F₂ + (1/h)F₁ · 1/(1 ± F₁d)               [12]\n\n"
     "or\n\n"
     "    F = { R₁ · 1/(1 ± R₁(1 − h)d) − R₂ } (1 − h)/h   [13]"),

    ("bounded by identical media on the two sides : — . . [14]",
     "bounded by identical media on the two sides:\n\n"
     "    V = U + F ;                                 [14]"),

    ("compared with the formula in current notation :",
     "compared with the formula in current notation:\n\n"
     "    1/v = 1/f − 1/u."),

    ("The difference in sign attributed to the term - arises",
     "The difference in sign attributed to the term 1/u arises"),

    # ---- Two thin lenses apart, and reflexion, printed pp. 67-69 ------
    ("at once gives us as the equivalent focal power, where /^ and F^ are "
     "the focal powers",
     "at once gives us as the equivalent focal power\n\n"
     "    F = F₂ + F₁ · 1/(1 + F₁d)                   [15]\n\n"
     "where F₁ and F₂ are the focal powers"),

    ("the sagitta AM of the initial curvature ; or V=-U . . . [16]",
     "the sagitta AM of the initial curvature; or\n\n"
     "    V = − U                                     [16]"),

    ("as it would have taken to reach A. Hence",
     "as it would have taken to reach A. Hence\n\n"
     "    BM = AM,\n\nor\n\n    BA = 2AM."),

    ("BA = 2AM. But AM measures the curvature of the mirror",
     "But AM measures the curvature of the mirror"),

    ("F=2.R . . [17]", "    F = 2R                                     [17]"),

    ("F will be in dioptrics if F^ and F^ are in dioptries",
     "F will be in dioptries if F₁ and F₂ are in dioptries"),

    # Lecture Six: the caption of Fig. 157, which is set into the text,
    # splits the sentence it interrupts. There is no plate for 157, so the
    # caption leaves nothing behind but a stray capital.
    ("and therefore capable\n\nOf producing kindred effects",
     "and therefore capable of producing kindred effects"),

    # Lecture One: a footnote that runs over TWO pages, with a plate and a
    # page break inside it, is dealt three ways at once by the scanner —
    # its head lands in the middle of the sentence about paraffin wax, its
    # tail lands in the middle of the sentence about mirrors, and the body
    # sentence it interrupted is left in two halves. Reassembled here.
    ("This is because of the translucent or Either of these two forms of "
     "instrument here described'is preferable to the old-fashioned "
     "\"grease-spot\" photometer of Bunsen. But both are surpassed in "
     "accuracy by the precision - photometer of semi-opaque property of "
     "paraffin wax, which results in a diffusion of the light laterally.",
     "This is because of the translucent or semi-opaque property of "
     "paraffin wax, which results in a diffusion of the light laterally."),

    ("Let us pass on to the operation of reflecting light by means of "
     "mirrors. A piece of polished metal such as Brodhun and Lummer, which "
     "can, however, only be described here very briefly. It gives "
     "determinations that can be relied on to within one-half of one per "
     "cent. The two lights to be compared",
     "Footnote: Either of these two forms of instrument is preferable to "
     "the old-fashioned \"grease-spot\" photometer of Bunsen. But both are "
     "surpassed in accuracy by the precision-photometer of Brodhun and "
     "Lummer, which can, however, only be described here very briefly. It "
     "gives determinations that can be relied on to within one-half of one "
     "per cent. The two lights to be compared"),

    ("hence can judge very accurately as to whether they are equally "
     "illuminated or not.",
     "hence can judge very accurately as to whether they are equally "
     "illuminated or not.\n\nLet us pass on to the operation of reflecting "
     "light by means of mirrors. A piece of polished metal such as"),

    # TABLE I, printed p. 73. Like the wave-length table of appendix four,
    # the OCR keeps the numbers but loses the columns entirely — every cell
    # becomes its own paragraph. Rebuilt here as an indented block. The
    # arithmetic checks: this table converts at 2.5 micro-centimetres to the
    # millionth of an inch throughout, a round figure rather than the 2.54
    # the appendix uses. Both are as printed; they are not harmonized.
    ("""NAME OF COLOUR.

Wave-length in millionths of Wave-length in millionths of a You will note""",
     """    Name of colour        Wave-length in     Wave-length in
                          millionths of      millionths of a
                          an inch            centimetre
    ------------------------------------------------------------
    Extremest red              32.4               81.0
    Red                        26.0               65.0
    Orange                     23.3               58.3
    Yellow                     22.0               55.1
    Green                      20.5               51.2
    Peacock                    19.0               47.5
    Blue                       18.0               44.9
    Violet                     16.0               40.0
    Extreme violet             14.4               36.0

You will note"""),

    # TABLE II, printed p. 92. Two columns, flattened by the scanner into a
    # single stream of cells with the ditto marks stranded between them.
    # Rebuilt from the page image and checked against the physics: orange
    # pairs with turquoise and yellow with blue, which is what the printed
    # table says and what the colour theory requires.
    ("""TABLE II. — COMPLEMENTARY TINTS

Crimson is complementary to Scarlet „

Moss green Peacock

Orange ,, Yellow""",
     """Table II — Complementary Tints

    Crimson is complementary to     Moss green
    Scarlet          "              Peacock
    Orange           "              Turquoise
    Yellow           "              Blue
    Primrose         "              Violet
    Green-yellow     "              Purple"""),

    # TABLE III, printed p. 108 — the eight ways of polarising light. The
    # scanner keeps every cell but loses the grid, so the grouping labels
    # end up stranded from the instruments they group. Rebuilt with the
    # eight instruments back under their five mechanisms; Thompson's own
    # sentence below the table ("some eight different ways") is the check.
    ("""By Reflexion .

Black glass at about 57° Delezenne's Polariser .

By Refraction . -|

Glass sheet at about 57° Bundle of thin glass sheets set obliquely

By Double Refraction -I

Rhomb of Iceland Spar Double-image Prism .

(p. 120). (p. 125).

By Double Refraction,) with Absorption . /

Slice of Tourmaline .

By Double Refraction, \\

Nicol's Prism and its with Internal Reflexion / modern Varieties .""",
     """    How it works                    Apparatus
    ---------------------------------------------------------
    By reflection                   Black glass at about 57°
                                    Delezenne's polariser
    By refraction                   Glass sheet at about 57°
                                    Bundle of thin glass sheets
                                      set obliquely
    By double refraction            Rhomb of Iceland spar (p. 120)
                                    Double-image prism (p. 125)
    By double refraction,           Slice of tourmaline
      with absorption
    By double refraction, with      Nicol's prism and its modern
      internal reflection             varieties"""),

    # Lecture Three: three more footnotes that run over a page break, each
    # of them landing its tail in the middle of the body sentence that was
    # running past it at the time. Same repair as the photometer footnote
    # in Lecture One.
    ("but they illusin POLARISATION OF LIGHT 125 trate what is meant",
     "but they illustrate what is meant"),

    ("What tint ought it to give ? Subin POLARISATION OF LIGHT 147 tracting "
     "13 millionths",
     "What tint ought it to give ? Subtracting 13 millionths"),

    ("Prisms made in Nicol's way that is also a principal plane, and these "
     "wedges are then reunited with Canada balsam or linseed oil. In a "
     "cheaper modification",
     "that is also a principal plane, and these wedges are then reunited "
     "with Canada balsam or linseed oil. In a cheaper modification"),

    ("they are finally reunited by balsam along two of their natural faces.",
     "they are finally reunited by balsam along two of their natural "
     "faces.\n\nPrisms made in Nicol's way"),

    ("is simply a large Nicol prism.1 patent plate glass to increase the "
     "intensity of the light.",
     "is simply a large Nicol prism."),

    ("covered by a single sheet of the thinnest",
     "covered by a single sheet of the thinnest patent plate glass to "
     "increase the intensity of the light. Fig. 85"),

    ("shows the design of this prism.", "shows the design of this prism."),

    # TABLE IV, printed p. 140 — Newton's colours of thin films. Same
    # damage as Tables I to III: the cells survive, the grid does not, and
    # the roman numerals that group the orders end up stranded in the
    # middle of the groups they label (the brace was vertically centred).
    # Rebuilt from the page image; the orders check against Thompson's own
    # prose, which says the first order ends in dark purple at 11
    # millionths, the second at 22 and the third at 33.
    ("""TINTS OF NEWTON'S COLOURS OF THIN FILMS.

Tint in Reflected Light.

Pale Peacock. Pale Rose. Rose.

Pale Qreen. Pale Rose.""",
     """Table IV — Tints of Newton's Colours of Thin Films

    Order   Film thickness      Tint in reflected light
            (millionths of an inch)
    ---------------------------------------------------
      I.        0               Black
                3.5             Gray
                5.5             Whitish
                8               Straw
               10               Orange
               10.5             Brick red
               11               Dark purple
     II.       11.5             Violet
               13               Blue
               15               Peacock
               18               Yellow
               19.5             Orange
               21               Red
               22               Violet
    III.       24               Blue
               25.5             Peacock
               27               Green
               29.5             Yellowish green
               31               Rose
               32.5             Crimson
               33               Purple
     IV.       34.5             Violet
               36               Peacock
               38               Green
               40               Yellowish green
               44               Rose
      V.       48               Pale green
               52               Pale rose
               55               Rose
     VI.       60               Pale peacock
               64               Pale rose
               66               Rose
    VII.       71               Pale green
               74               Pale rose"""),

    # The axis labels printed inside Fig. 96 fall into the sentence running
    # past it.
    ("the air-gap being supposed to widen in Thickness of film",
     "the air-gap being supposed to widen in"),
    ("I I f V VI\n\nMillionths of Inch 0 proportion to the radius.",
     "proportion to the radius."),

    # Appendix to Lecture Three. Newton's law for the velocity of a wave,
    # flattened to "-v — v/ E-f-D". The sentence states it in words in the
    # same breath, which is what makes the reading certain.
    ("as expressed in symbols, -v — v/ E-f-D, which is Newton's law",
     "as expressed in symbols, v = √(E/D), which is Newton's law"),
    ("The only other poi. \\l£it need claim attention here",
     "The only other point that need claim attention here"),
    ("the line along which th wave is being propagated (i.e. the \"ray\" "
     "lies in this p, •**.)",
     "the line along which the wave is being propagated (that is, the "
     "\"ray\" lies in this plane)"),
    ("in the Appendix to Lecture V 'p. 230).",
     "in the Appendix to Lecture Five, p. 230."),
    ("plane of polarisation,'5 that of MacCullagh",
     'plane of polarisation," that of MacCullagh'),

    ("of too great a wave- Mi length — to affect our eyes",
     "of too great a wave-length — to affect our eyes"),

    # TABLE V, printed p. 175 — Wiedemann's classification of luminescence.
    # The scanner keeps the two columns but shuffles them past each other,
    # and DROPS three whole rows whose cells were too short to survive the
    # paragraph filter: tribo-luminescence, the two halves of electro-
    # luminescence, lyo-luminescence, and the single substance under
    # crystallo-luminescence (arsenious acid). Rebuilt from the page image.
    # Thompson refers back to this list by number in Lecture Six, so the
    # numbering is load-bearing.
    ('Substance in which it occurs.\n\n2. Photo-luminescence :\n\n(n) transient— Fluorescence (b} persistent = Phosphorescence\n\n3. Thermo-luminescence .\n\n5. Electro-luminescence :\n\n6. Crystallo-luminescence .\n\n8. X-luminescence , Phosphorus oxidising in moist air ; decaying wood ; decaying fish ; glow-worm ; firefly; marine organisms, etc.\n\nFluor-spar ; uranium - glass ; quinine ; scheelite ; platinocyanides of " -io"- bases ; eosin and many coai-tar products.\n\nBologna-stone ; Canton\'s phosphorus and other sulphides of alkaline earths ; some diamonds, etc.\n\nFluor-spar ; scheelite.\n\nDiamo: Js ; sugar ; quartz ; uranyl nitrate ; pentadecylparatolylketone.\n\nMany rarefied gases ; many of the fluorescent and phosphorescent bodies.\n\n•Rubies ; glass ; diamonds ; many gems and minerals.\n\nSub - chlorides of alkalimetals.\n\nPlatino-cyanides ; scheelite, etc.',
     "    Phenomenon                    Substance in which it occurs\n    ------------------------------------------------------------------\n    1. Chemi-luminescence         Phosphorus oxidising in moist air;\n                                  decaying wood; decaying fish;\n                                  glow-worm; firefly; marine\n                                  organisms, etc.\n    2. Photo-luminescence:\n       (a) transient =            Fluor-spar; uranium-glass; quinine;\n           Fluorescence           scheelite; platinocyanides of\n                                  various bases; eosin and many\n                                  coal-tar products.\n       (b) persistent =           Bologna-stone; Canton's phosphorus\n           Phosphorescence        and other sulphides of alkaline\n                                  earths; some diamonds, etc.\n    3. Thermo-luminescence        Fluor-spar; scheelite.\n    4. Tribo-luminescence         Diamonds; sugar; quartz; uranyl\n                                  nitrate; pentadecylparatolylketone.\n    5. Electro-luminescence:\n       (a) Effluvio-              Many rarefied gases; many of the\n           luminescence           fluorescent and phosphorescent\n                                  bodies.\n       (b) Kathodo-               Rubies; glass; diamonds; many gems\n           luminescence           and minerals.\n    6. Crystallo-luminescence     Arsenious acid.\n    7. Lyo-luminescence           Sub-chlorides of alkali metals.\n    8. X-luminescence             Platino-cyanides; scheelite, etc."),

    # The three-line legend printed inside Fig. 105 falls into the sentence
    # running past it.
    ("blue-violet light falls through x. To be illuminated by Blue-Violet "
     "Light. 2. To be illuminated by Green Light. 3. To be illuminated by "
     "Red Light.",
     "blue-violet light falls through"),

    ("whether the face of the thermopil e is warmer",
     "whether the face of the thermopile is warmer"),
    ("If it is warmer the will move to the right",
     "If it is warmer the spot will move to the right"),

    # Lecture Five: the damped-oscillation sketch printed inside the
    # footnote falls into the middle of the footnote's own sentence, and
    # Hertz's portrait caption falls into the middle of the body sentence
    # about drawing sparks off a door-knob.
    ("A mechanical analogy may be found in the vibrations of a spring "
     "denly release it.",
     "A mechanical analogy may be found in the vibrations of a spring. "
     "Bend it to one side and suddenly release it."),
    ("Bend it on one side and sud- It flies backward and forward, the "
     "motion dying out after a certain number of swings.",
     "It flies backward and forward, the motion dying out after a certain "
     "number of swings."),
    ("hold a knife or pencil-case to the — PROFESSOR HEINRICH HERTZ.",
     "hold a knife or pencil-case to the"),
    ("the lower curve in This corresponds",
     "the lower curve in Fig. 118. This corresponds"),

    # The Bose footnote runs over three pages and swallows two body
    # sentences whole on its way. Untangled: the footnote gets its own text
    # back, and the lecture gets back its closing demonstration.
    ("But before I close I must show you at least some of in a metal tube "
     "projects from a box A, doubly cased in metal ;",
     "in a metal tube projects from a box A, doubly cased in metal;"),

    ("polarise the electric these effects in actual experiment. Here, in a "
     "metal box, is a small induction coil",
     "polarise the electric beam, since (like the tourmaline for short "
     "waves) these materials absorb the electric vibrations in directions "
     "parallel to certain axes of their structure. Even an ordinary book "
     "possesses a polarising structure for these waves; those that vibrate "
     "parallel to the leaves are absorbed more than those that vibrate "
     "across them.\n\nBut before I close I must show you at least some of "
     "these effects in actual experiment. Here, in a metal box, is a small "
     "induction coil"),

    ("Then I hold a plate of metal as a mirror beam, since (like the "
     "tourmaline for short waves) these materials absorb the electric "
     "vibrations in directions parallel' to certain axes of their "
     "structure. Even an ordinary book possesses for these waves a "
     "polarising structure ; the waves that vibrate parallel to the leaves "
     "being absorbed more than those that vibrate in a direction transverse "
     "to them.\n\nto reflect the waves",
     "Then I hold a plate of metal as a mirror to reflect the waves"),

    # The Crookes-pump footnote runs over the page and drops its tail into
    # the middle of the body sentence about the drying tube.
    ("A drying-tube, filled with method of connecting the pump with the "
     "object to be exhausted, by means of a thin, flexible, spiral glass "
     "tube ; the method of cleansing the fall-tube by letting in a little "
     "strong sulphuric acid through a stoppered valve in the head of the "
     "pump. In carrying out these developments Mr. Crookes was assisted by "
     "the late Mr. C. Gimingham, whose later contributions to the subject "
     "are described in the author's monograph on the Mercurial Air-pump.",
     "A drying-tube, filled with"),
    ("the use of an air-trap in the tube leading up to the pump-head ; the",
     "the use of an air-trap in the tube leading up to the pump-head; the "
     "method of connecting the pump with the object to be exhausted by a "
     "thin, flexible, spiral glass tube; and the method of cleansing the "
     "fall-tube by letting in a little strong sulphuric acid through a "
     "stoppered valve in the head of the pump. In carrying out these "
     "developments Mr. Crookes was assisted by the late Mr. C. Gimingham, "
     "whose later contributions to the subject are described in the "
     "author's monograph on the Mercurial Air-Pump."),
    ("hold a knife or pencil-case to the",
     "hold a knife or pencil-case to the"),

    # Lecture Six's aside on the neglect of science in England. Two long
    # footnotes run over two pages between them, and between them they
    # swallow the body sentence about what is expected of a professor, the
    # portrait caption of Rontgen, and the sentence about the London
    # charter. Reassembled: two footnotes, one argument.
    ("infinitely better than that of the University of London ; ' and it "
     "is — PROFESSOR W. K. RÖNTGEN.",
     "infinitely better than that of the University of London; and it is "
     "expected of the professor that he shall contribute to the "
     "advancement of science by original investigations."),

    ("temporary arrangements are made whenever an examination in practical",
     "temporary arrangements are made whenever an examination in practical "
     "physics is to be held. A curtain of black cloth slung across one end "
     "of the room gave partial obscurity over the tables where photometric "
     "and spectroscopic apparatus was placed. The third room, sometimes "
     "called the galvanometer room, is a smaller room in the basement, "
     "artificially lighted, and used chiefly for printing, except at the "
     "times of examinations in practical physics.\" Such is the melancholy "
     "state of things in a University where everything is sacrificed on "
     "the altar of competitive examinations."),

    ("expected of the professor that he shall contribute to the "
     "advancement of science by original investigations. With such "
     "material",
     "With such material"),

    ("Its charter physics is to be held. A curtain of black cloth slung "
     "across one end of the room gave partial obscurity over the tables "
     "where photometric and spectroscopic apparatus was placed. The third "
     "room, sometimes called the galvanometer room, is a smaller room in "
     "the basement, artificially lighted, and used chiefly for printing, "
     "except at the times of examinations in practical physics.\" Such is "
     "the melancholy state of things in a University where everything is "
     "sacrificed on the altar of competitive examinations.",
     "Its charter"),

    ("necessary funds. Its charter\n\nBavaria has a population",
     "necessary funds.\n\nFootnote: Bavaria has a population"),
    ("the room being used for examination purposes almost every day.\n\n"
     "precludes it from doing anything for science except hold "
     "examinations !",
     "the room being used for examination purposes almost every day.\n\n"
     "Its charter precludes it from doing anything for science except "
     "hold examinations!"),

    # Stokes's solitary-ripple theory, with a footnote dropped through the
    # middle of the sentence that states it, and a library stamp shouldering
    # in among the plate captions.
    ("solitary ripples, each of not more than one or There can be no "
     "question that these rays, which are due to a sort of invisible "
     "phosphorescence, consist of transverse vibrations of a very high "
     "frequency : that is, they are ultra-violet light of a very high "
     "order.",
     "solitary ripples, each of not more than one or\n\nFootnote: There can "
     "be no question that these rays, which are due to a sort of invisible "
     "phosphorescence, consist of transverse vibrations of a very high "
     "frequency: that is, they are ultra-violet light of a very high "
     "order."),
    ("OF THB **F\n\n", ""),

    ("In Cambridge notation",
     "In Cambridge notation\n\n    1/f = 2/r,\n\nor\n\n    f = r/2."),

    ("In symbols, y=_U+F . . [18]",
     "In symbols,\n\n"
     "    V = − U + F                                 [18]"),
    # ---- Appendix to Lecture II: anomalous dispersion, printed pp. 100-104
    # The von Helmholtz formula vanished outright, leaving the sentence to
    # promise "the following" and then show nothing. Read off printed p. 103.
    # Greek letters fare worst of all in this scan: mu comes through as
    # "/x", "[j.", "yu," and "//,"; beta as "ft", "/3" and "j3".
    ("was first noticed l in 1840", "was first noticed in 1840"),
    ("See Tail's Light, p. 156.", "See Tait's Light, p. 156."),
    ("See Wudemands Annalen, xlviii. p. 389.",
     "See Wiedemann's Annalen, xlviii. p. 389."),
    ("ib. p. 37i~(JuTy 1896).", "ib. p. 371 (July 1896)."),

    ("The formula which von Helmholtz deduced is in its simplest form the "
     "following : — where /x, is the refractive index of the medium "
     "(supposed quite transparent), n the frequency, and a and ft constants "
     "depending on the material.",
     "The formula which von Helmholtz deduced is, in its simplest form, the "
     "following:\n\n"
     "    μ² = (α² − n²) / (β² − n²)\n\n"
     "where μ is the refractive index of the medium (supposed quite "
     "transparent), n the frequency, and α and β constants depending on "
     "the material."),

    ("in the following cases (i) n much smaller than a or ft ; (2) n — ft ; "
     "(3) ;/ = a; and (4) n much greater than a or /3.",
     "in the following cases: (1) n much smaller than α or β; (2) n = β; "
     "(3) n = α; and (4) n much greater than α or β."),

    ("Neglecting rfi compared with a2 or ft the formula reduces to "
     "[j. = a//?, being independent of wave-length.",
     "Neglecting n² compared with α² or β², the formula reduces to "
     "μ = α/β, being independent of wave-length."),

    ("if the frequency is such that n = ft the medium",
     "if the frequency is such that n = β the medium"),
    ("toward the value n = ft the refractive index",
     "toward the value n = β the refractive index"),
    ("where n is larger than ft but smaller than a, the values of yu, "
     "calculated by the formula are imaginary ; but owing to the absorption "
     "they would in reality diminish clown to near zero",
     "where n is larger than β but smaller than α, the values of μ "
     "calculated by the formula are imaginary; but owing to the absorption "
     "they would in reality diminish down to near zero"),
    ("As n increases from case (3) when it equals a, the zero value of /x "
     "gradually changes, and, when n becomes very great compared with a and "
     "j3, it approaches to unity",
     "As n increases from case (3) when it equals α, the zero value of μ "
     "gradually changes, and, when n becomes very great compared with α and "
     "β, it approaches to unity"),

    ("Consider the particular value of n for which /x becomes a maximum.",
     "Consider the particular value of n for which μ becomes a maximum."),
    ("in the wrong direction (/x being less than unity)",
     "in the wrong direction (μ being less than unity)"),
    ("Fig. 63 illustrates this dependence of //, upon n.",
     "Fig. 63 illustrates this dependence of μ upon n."),
]
