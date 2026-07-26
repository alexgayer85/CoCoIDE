***********************************************************************
* Sea Battle ML — CoCo 1/2/3 · PMODE 4 dual boards · matrix keyboard
*
* Loader (main.bas):
*   CLEAR200,&H3F00 : PCLEAR4 : PMODE4,1 : PCLS : SCREEN1,1
*   LOADM"SEA" : EXEC
*
* Controls (no typed coords — reliable under XRoar):
*   WASD / arrows  move cursor
*   Space / Enter  fire or place
*   R              rotate ship (placement)
*   A              auto-place remaining fleet
*   F              (battle) flash own fleet highlight only — boards stay dual
***********************************************************************

* Hardware
PIA0    equ     $FF00           ; keyboard rows (R)
PIA0D   equ     $FF02           ; keyboard columns (W)
DAC     equ     $FF20
PIA1CRA equ     $FF01
PIA1CRB equ     $FF03
PIA2CRB equ     $FF23

* PMODE 4 page 1 (after PCLEAR 4 / PMODE 4,1)
GFX     equ     $0E00
GROWS   equ     192
GBPL    equ     32              ; bytes per line

* Board geometry — CELL=8 so each cell row is exactly one PM4 byte (fast)
CELL    equ     8
* Left fleet board (X must stay multiple of 8)
LX0     equ     16
LY0     equ     24
* Right radar board
RX0     equ     144
RY0     equ     24

        org     $3F00

***********************************************************************
START
        clra
        tfr     a,dp
        lbsr    SoundInit
        lbsr    SeedRnd
        lbsr    InitGame
        lbsr    TitleScreen
        lbsr    InstructScreen
        lbsr    PlacePlayerFleet
        lbsr    PlaceEnemyFleet
        lbsr    BattleLoop
        lbsr    GameOver
        rts

***********************************************************************
* Init grids / ships
***********************************************************************
InitGame
        ldx     #PS
        lbsr    Clear100
        ldx     #ES
        lbsr    Clear100
        ldx     #RD
        lbsr    Clear100
        ldx     #AK
        lbsr    Clear100
        * ship lengths / remaining (explicit stores)
        ldx     #SL
        lda     #5
        sta     ,x+
        lda     #4
        sta     ,x+
        lda     #3
        sta     ,x+
        sta     ,x+
        lda     #2
        sta     ,x+
        ldx     #SR
        lda     #5
        sta     ,x+
        lda     #4
        sta     ,x+
        lda     #3
        sta     ,x+
        sta     ,x+
        lda     #2
        sta     ,x+
        lda     #17
        sta     PH
        sta     EH
        clr     Hunt
        clr     HR
        clr     HC
        lda     #1
        sta     CurR
        sta     CurC
        clr     Horiz
        rts

Clear100
        ldb     #100
c1      clr     ,x+
        decb
        bne     c1
        rts

***********************************************************************
* Title — main.bas does LOADM"SEA" then LOADM"NAVAL" then EXEC.
* NAVAL is last so the art is already on $0E00 when we start; we only
* draw the bottom bar (no 6K blit). SEA no longer embeds the splash.
***********************************************************************
TitleScreen
        * dark bar so text is readable on busy art
        lda     #176
        ldb     #16
        lbsr    ClearRows
        leax    TCopy,pcr
        lda     #48
        ldb     #180
        lbsr    DrawStr
        lbsr    PauseLong
        lbsr    PauseMed
        lda     #176
        ldb     #16
        lbsr    ClearRows
        leax    TGo,pcr
        lda     #40
        ldb     #180
        lbsr    DrawStr
        lbsr    WaitKey
        rts

* A=startY B=rows — black bar on GFX page
ClearRows
        pshs    a,b,x
        sta     TY
        stb     Ht
cr_r    lda     TY
        ldb     #GBPL
        mul
        tfr     d,x
        leax    GFX,x
        ldb     #32
        clra
cr_c    sta     ,x+
        decb
        bne     cr_c
        inc     TY
        dec     Ht
        bne     cr_r
        puls    a,b,x
        rts

***********************************************************************
* Instructions (second page before placement)
***********************************************************************
InstructScreen
        lbsr    GfxCls
        leax    TI0,pcr
        lda     #8
        ldb     #4
        lbsr    DrawStr
        leax    TI1,pcr
        lda     #8
        ldb     #24
        lbsr    DrawStr
        leax    TI2,pcr
        lda     #8
        ldb     #36
        lbsr    DrawStr
        leax    TI3,pcr
        lda     #8
        ldb     #48
        lbsr    DrawStr
        leax    TI4,pcr
        lda     #8
        ldb     #60
        lbsr    DrawStr
        leax    TI5,pcr
        lda     #8
        ldb     #80
        lbsr    DrawStr
        leax    TI6,pcr
        lda     #8
        ldb     #92
        lbsr    DrawStr
        leax    TI7,pcr
        lda     #8
        ldb     #104
        lbsr    DrawStr
        leax    TI8,pcr
        lda     #8
        ldb     #124
        lbsr    DrawStr
        leax    TI9,pcr
        lda     #8
        ldb     #136
        lbsr    DrawStr
        leax    TGo,pcr
        lda     #40
        ldb     #168
        lbsr    DrawStr
        lbsr    WaitKey
        rts

***********************************************************************
* Placement
***********************************************************************
PlacePlayerFleet
        lda     #1
        sta     ShipId
        lda     #1
        sta     Horiz           ; start horizontal (whole ship visible)
        lda     #1
        sta     CurR
        sta     CurC
pp_loop
        lda     ShipId
        cmpa    #6
        lbhs    pp_done
pp_draw
        lbsr    DrawBoardsOnly
        lbsr    DrawPlaceHUD
        lbsr    DrawScores
        lbsr    ClampShip
        lbsr    DrawGhostShip   ; full ship preview at cursor
pp_in
        lbsr    WaitKey
        tsta
        lbeq    pp_in
        cmpa    #'D
        lbeq    pp_r
        cmpa    #'d
        lbeq    pp_r
        cmpa    #'A
        lbeq    pp_l
        cmpa    #'a
        lbeq    pp_l
        cmpa    #'S
        lbeq    pp_dn
        cmpa    #'s
        lbeq    pp_dn
        cmpa    #'W
        lbeq    pp_u
        cmpa    #'w
        lbeq    pp_u
        cmpa    #'L
        lbeq    pp_r
        cmpa    #'l
        lbeq    pp_r
        cmpa    #'J
        lbeq    pp_l
        cmpa    #'j
        lbeq    pp_l
        cmpa    #'I
        lbeq    pp_u
        cmpa    #'i
        lbeq    pp_u
        cmpa    #'K
        lbeq    pp_dn
        cmpa    #'k
        lbeq    pp_dn
        cmpa    #9
        lbeq    pp_r
        cmpa    #8
        lbeq    pp_l
        cmpa    #10
        lbeq    pp_dn
        cmpa    #94
        lbeq    pp_u
        cmpa    #12
        lbeq    pp_u
        cmpa    #11
        lbeq    pp_u
        cmpa    #30
        lbeq    pp_u
        cmpa    #28
        lbeq    pp_u
        cmpa    #'^
        lbeq    pp_u
        cmpa    #'R
        lbeq    pp_rot
        cmpa    #'r
        lbeq    pp_rot
        cmpa    #'P
        lbeq    pp_auto
        cmpa    #'p
        lbeq    pp_auto
        cmpa    #'0
        lbeq    pp_auto
        cmpa    #32
        lbeq    pp_put
        cmpa    #13
        lbeq    pp_put
        lbra    pp_in
pp_rot
        lbsr    UndrawGhostShip
        lda     Horiz
        eora    #1
        sta     Horiz
        lbsr    ClampShip
        lbsr    DrawGhostShip
        lbsr    DrawPlaceHUD    ; refresh HORIZ/VERT label
        lbra    pp_in
pp_r    lbsr    UndrawGhostShip
        lda     CurC
        cmpa    #10
        bhs     pp_rm
        inc     CurC
pp_rm   lbsr    ClampShip
        lbsr    DrawGhostShip
        lbra    pp_in
pp_l    lbsr    UndrawGhostShip
        lda     CurC
        cmpa    #1
        bls     pp_lm
        dec     CurC
pp_lm   lbsr    ClampShip
        lbsr    DrawGhostShip
        lbra    pp_in
pp_dn   lbsr    UndrawGhostShip
        lda     CurR
        cmpa    #10
        bhs     pp_dm
        inc     CurR
pp_dm   lbsr    ClampShip
        lbsr    DrawGhostShip
        lbra    pp_in
pp_u    lbsr    UndrawGhostShip
        lda     CurR
        cmpa    #1
        bls     pp_um
        dec     CurR
pp_um   lbsr    ClampShip
        lbsr    DrawGhostShip
        lbra    pp_in

ClampCur
        lda     CurR
        bne     cc1
        lda     #1
cc1     cmpa    #10
        bls     cc2
        lda     #10
cc2     sta     CurR
        lda     CurC
        bne     cc3
        lda     #1
cc3     cmpa    #10
        bls     cc4
        lda     #10
cc4     sta     CurC
        rts

* Keep whole ship (length TmpL / ShipId) on the 10x10 board
ClampShip
        pshs    a,b
        lbsr    ShipLen
        stb     TmpL
        lbsr    ClampCur
        tst     Horiz
        beq     cs_v
        lda     CurC
        adda    TmpL
        deca
        cmpa    #10
        bls     cs_x
        lda     #11
        suba    TmpL
        sta     CurC
        bra     cs_x
cs_v    lda     CurR
        adda    TmpL
        deca
        cmpa    #10
        bls     cs_x
        lda     #11
        suba    TmpL
        sta     CurR
cs_x    puls    a,b
        rts

***********************************************************************
* Ghost ship: draw/erase full ship footprint during placement.
* Checker pattern = preview; placed ships use solid hull art.
***********************************************************************
DrawGhostShip
        pshs    a,b,x
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lbsr    ShipLen
        stb     TmpL
        clr     TmpI
dgs_l   lda     TmpI
        cmpa    TmpL
        bhs     dgs_x
        lda     CurR
        ldb     CurC
        tst     Horiz
        beq     dgs_v
        addb    TmpI
        bra     dgs_b
dgs_v   adda    TmpI
dgs_b   sta     RR
        stb     CC
        lbsr    CellOrigin
        leax    PatGhost,pcr
        lbsr    CellBlit
        inc     TmpI
        bra     dgs_l
dgs_x   puls    a,b,x
        rts

UndrawGhostShip
        pshs    a,b,x
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lbsr    ShipLen
        stb     TmpL
        clr     TmpI
ugs_l   lda     TmpI
        cmpa    TmpL
        bhs     ugs_x
        lda     CurR
        ldb     CurC
        tst     Horiz
        beq     ugs_v
        addb    TmpI
        bra     ugs_b
ugs_v   adda    TmpI
ugs_b   sta     RR
        stb     CC
        lbsr    DrawOneCell     ; restore water / placed ships
        inc     TmpI
        bra     ugs_l
ugs_x   puls    a,b,x
        rts

pp_put
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        clr     TmpG
        lbsr    ShipLen
        stb     TmpL
        lda     TmpL
        beq     pp_bad
        lbsr    CanPlace
        lda     CP
        beq     pp_bad
        clr     TmpG
        lbsr    PlaceShipRaw
        inc     ShipId
        lda     ShipId
        cmpa    #6
        lbhs    pp_done
        * next ship: full redraw + new ghost
        lda     #1
        sta     CurR
        sta     CurC
        lbra    pp_draw
pp_bad
        lbra    pp_in
pp_auto
        lbsr    AutoPlacePlayer
        lda     #6
        sta     ShipId
pp_done
        lbsr    DrawBoardsOnly
        rts

DrawPlaceHUD
        * Wipe full glyph height (8 rows each). Clearing only to y=17 left
        * scanlines 18-19 of the ship line dirty — bottom of HORIZ's Z
        * showed as "_" after switching to VERT.
        lda     #2
        ldb     #8              ; title line y=2..9
        lbsr    ClearRows
        lda     #12
        ldb     #8              ; ship/orient line y=12..19
        lbsr    ClearRows
        lda     #180
        ldb     #8              ; status line y=180..187
        lbsr    ClearRows
        leax    TPlace,pcr
        lda     #8
        ldb     #2
        lbsr    DrawStr
        * current craft name (max BATTLESHIP = 10 glyphs)
        lda     ShipId
        cmpa    #1
        beq     dph1
        cmpa    #2
        beq     dph2
        cmpa    #3
        beq     dph3
        cmpa    #4
        beq     dph4
        leax    TNDest,pcr
        bra     dphn
dph1    leax    TNCarr,pcr
        bra     dphn
dph2    leax    TNBatt,pcr
        bra     dphn
dph3    leax    TNCrui,pcr
        bra     dphn
dph4    leax    TNSub,pcr
dphn    lda     #8
        ldb     #12
        lbsr    DrawStr
        * orientation — fixed column after longest name
        tst     Horiz
        beq     dphv
        leax    TH,pcr
        bra     dpho
dphv    leax    TV,pcr
dpho    lda     #104
        ldb     #12
        lbsr    DrawStr
        * short hint: must fit in 256px (≤30 chars from x=8)
        leax    THint,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        rts

PlaceEnemyFleet
        lbsr    GfxCls
        leax    TComp,pcr
        lda     #40
        ldb     #90
        lbsr    DrawStr
        lda     #1
        lbsr    AutoPlaceFleet
        rts

***********************************************************************
* Auto-place — NO CanPlace/Rand loops (those froze on P).
* Pure linear stores. 8 distinct layouts via Rnd (entropy from WaitKey).
* Player → PS, Enemy → ES
***********************************************************************
AutoPlacePlayer
        ldx     #PS
        bra     AutoFillGrid

AutoPlaceFleet
        * A ignored; enemy always ES
        ldx     #ES
        * fall through
AutoFillGrid
        * X = base of 100-byte grid; keep base in U
        tfr     x,u
        ldb     #100
af_cl   clr     ,x+
        decb
        bne     af_cl
        * spin RNG so player vs enemy (and re-runs) differ
        lbsr    Rand
        lbsr    Rand
        lbsr    Rand
        lda     Rnd
        anda    #7
        lbeq    afl0
        cmpa    #1
        lbeq    afl1
        cmpa    #2
        lbeq    afl2
        cmpa    #3
        lbeq    afl3
        cmpa    #4
        lbeq    afl4
        cmpa    #5
        lbeq    afl5
        cmpa    #6
        lbeq    afl6
        lbra    afl7

* 0: top-left pack
afl0    tfr     u,x
        lda     #1
        sta     0,x
        sta     1,x
        sta     2,x
        sta     3,x
        sta     4,x
        lda     #2
        sta     10,x
        sta     11,x
        sta     12,x
        sta     13,x
        lda     #3
        sta     20,x
        sta     21,x
        sta     22,x
        lda     #4
        sta     40,x
        sta     41,x
        sta     42,x
        lda     #5
        sta     60,x
        sta     61,x
        lbra    af_done

* 1: bottom-right pack
afl1    tfr     u,x
        lda     #1
        sta     55,x
        sta     56,x
        sta     57,x
        sta     58,x
        sta     59,x
        lda     #2
        sta     75,x
        sta     76,x
        sta     77,x
        sta     78,x
        lda     #3
        sta     85,x
        sta     86,x
        sta     87,x
        lda     #4
        sta     93,x
        sta     94,x
        sta     95,x
        lda     #5
        sta     98,x
        sta     99,x
        lbra    af_done

* 2: top-right carrier + left verticals
afl2    tfr     u,x
        lda     #1
        sta     5,x
        sta     6,x
        sta     7,x
        sta     8,x
        sta     9,x
        lda     #2
        sta     20,x
        sta     30,x
        sta     40,x
        sta     50,x
        lda     #3
        sta     22,x
        sta     32,x
        sta     42,x
        lda     #4
        sta     70,x
        sta     71,x
        sta     72,x
        lda     #5
        sta     90,x
        sta     91,x
        lbra    af_done

* 3: bottom-left + top mid
afl3    tfr     u,x
        lda     #1
        sta     90,x
        sta     91,x
        sta     92,x
        sta     93,x
        sta     94,x
        lda     #2
        sta     3,x
        sta     4,x
        sta     5,x
        sta     6,x
        lda     #3
        sta     25,x
        sta     26,x
        sta     27,x
        lda     #4
        sta     48,x
        sta     58,x
        sta     68,x
        lda     #5
        sta     80,x
        sta     81,x
        lbra    af_done

* 4: four corners scatter
afl4    tfr     u,x
        lda     #1
        sta     0,x
        sta     10,x
        sta     20,x
        sta     30,x
        sta     40,x
        lda     #2
        sta     9,x
        sta     19,x
        sta     29,x
        sta     39,x
        lda     #3
        sta     70,x
        sta     71,x
        sta     72,x
        lda     #4
        sta     96,x
        sta     97,x
        sta     98,x
        lda     #5
        sta     55,x
        sta     56,x
        lbra    af_done

* 5: mid band (was a broken "cross" — battleship skipped over carrier
*     and ship4 was an L at 8/9/18). All straight, no overlaps.
afl5    tfr     u,x
        lda     #1              ; carrier row4 cols0-4
        sta     40,x
        sta     41,x
        sta     42,x
        sta     43,x
        sta     44,x
        lda     #2              ; battleship col6 rows0-3
        sta     6,x
        sta     16,x
        sta     26,x
        sta     36,x
        lda     #3              ; cruiser row6 cols0-2
        sta     60,x
        sta     61,x
        sta     62,x
        lda     #4              ; sub row8 cols5-7
        sta     85,x
        sta     86,x
        sta     87,x
        lda     #5              ; destroyer row2 cols8-9
        sta     28,x
        sta     29,x
        lbra    af_done

* 6: right edge wall + bottom
afl6    tfr     u,x
        lda     #1
        sta     9,x
        sta     19,x
        sta     29,x
        sta     39,x
        sta     49,x
        lda     #2
        sta     80,x
        sta     81,x
        sta     82,x
        sta     83,x
        lda     #3
        sta     0,x
        sta     1,x
        sta     2,x
        lda     #4
        sta     55,x
        sta     56,x
        sta     57,x
        lda     #5
        sta     73,x
        sta     74,x
        lbra    af_done

* 7: checker-ish spread
afl7    tfr     u,x
        lda     #1
        sta     11,x
        sta     12,x
        sta     13,x
        sta     14,x
        sta     15,x
        lda     #2
        sta     37,x
        sta     47,x
        sta     57,x
        sta     67,x
        lda     #3
        sta     70,x
        sta     71,x
        sta     72,x
        lda     #4
        sta     4,x
        sta     5,x
        sta     6,x
        lda     #5
        sta     93,x
        sta     94,x
af_done lbsr    Rand
        lbsr    Rand
        rts

* ShipId (1..5) → B = length
ShipLen
        pshs    a,x
        lda     ShipId
        beq     sl0
        cmpa    #5
        bls     sl1
        lda     #5
sl1     deca
        leax    LenTab,pcr
        lda     a,x
        tfr     a,b
        puls    a,x
        rts
sl0     ldb     #2
        puls    a,x
        rts

LenTab  fcb     5,4,3,3,2

***********************************************************************
* CanPlace / PlaceShip / CellAddr
***********************************************************************
CanPlace
        lda     #1
        sta     CP
        clr     TmpI
cpl     lda     TmpI
        cmpa    TmpL
        bhs     cpo
        lda     TmpR
        ldb     TmpC
        tst     Horiz
        beq     cpv
        addb    TmpI
        bra     cpb
cpv     adda    TmpI
cpb     tsta
        beq     cpf
        cmpa    #10
        bhi     cpf
        tstb
        beq     cpf
        cmpb    #10
        bhi     cpf
        sta     RR
        stb     CC
        lda     TmpG
        bne     cpe
        ldx     #PS
        bra     cpx
cpe     ldx     #ES
cpx     lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        bne     cpf
        inc     TmpI
        bra     cpl
cpf     clr     CP
cpo     rts

PlaceShip
        sta     TmpG
        stb     ShipId
        lbsr    ShipLen
        stb     TmpL
PlaceShipRaw
        * uses TmpG, ShipId, TmpR, TmpC, Horiz, TmpL
        clr     TmpI
psl     lda     TmpI
        cmpa    TmpL
        bhs     psx
        lda     TmpR
        ldb     TmpC
        tst     Horiz
        beq     psv
        addb    TmpI
        bra     psb
psv     adda    TmpI
psb     sta     RR
        stb     CC
        lda     TmpG
        bne     pse
        ldx     #PS
        bra     psw
pse     ldx     #ES
psw     lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ShipId
        sta     ,x
        inc     TmpI
        bra     psl
psx     rts

* X=base A=row1-10 B=col1-10 → X=&cell
CellAddr
        deca
        decb
        pshs    b
        ldb     #10
        mul
        addb    ,s+
        abx
        rts

***********************************************************************
* Battle
***********************************************************************
BattleLoop
bl      lda     EH
        lbeq    bld
        lda     PH
        lbeq    bld
        lbsr    PlayerTurn
        lda     EH
        lbeq    bld
        lbsr    ComputerTurn
        lda     PH
        lbeq    bld
        lbra    bl
bld     rts

PlayerTurn
pt_d    lbsr    DrawBattle      ; boards + battle HUD + scores
        lbsr    DrawCursorRight
pt_i    lbsr    WaitKey
        tsta
        lbeq    pt_i
        cmpa    #'F
        lbeq    pt_d
        cmpa    #'f
        lbeq    pt_d
        cmpa    #'D
        lbeq    pt_r
        cmpa    #'d
        lbeq    pt_r
        cmpa    #'L
        lbeq    pt_r
        cmpa    #'l
        lbeq    pt_r
        cmpa    #9
        lbeq    pt_r
        cmpa    #'A
        lbeq    pt_l
        cmpa    #'a
        lbeq    pt_l
        cmpa    #'J
        lbeq    pt_l
        cmpa    #'j
        lbeq    pt_l
        cmpa    #8
        lbeq    pt_l
        cmpa    #'S
        lbeq    pt_dn
        cmpa    #'s
        lbeq    pt_dn
        cmpa    #10
        lbeq    pt_dn
        cmpa    #'W
        lbeq    pt_up
        cmpa    #'w
        lbeq    pt_up
        cmpa    #'I
        lbeq    pt_up
        cmpa    #'i
        lbeq    pt_up
        cmpa    #'K
        lbeq    pt_dn
        cmpa    #'k
        lbeq    pt_dn
        cmpa    #94
        lbeq    pt_up
        cmpa    #12
        lbeq    pt_up
        cmpa    #11
        lbeq    pt_up
        cmpa    #30
        lbeq    pt_up
        cmpa    #28
        lbeq    pt_up
        cmpa    #'^
        lbeq    pt_up
        cmpa    #32
        lbeq    pt_fire
        cmpa    #13
        lbeq    pt_fire
        lbra    pt_i
pt_r    lda     CurC
        cmpa    #10
        lbhs    pt_i
        lbsr    UndrawCursorRight
        inc     CurC
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_l    lda     CurC
        cmpa    #1
        lbls    pt_i
        lbsr    UndrawCursorRight
        dec     CurC
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_dn   lda     CurR
        cmpa    #10
        lbhs    pt_i
        lbsr    UndrawCursorRight
        inc     CurR
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_up   lda     CurR
        cmpa    #1
        lbls    pt_i
        lbsr    UndrawCursorRight
        dec     CurR
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_fire
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        lda     #1
        lbsr    ApplyShot
        * show shot result on radar — no solid cursor on top (it hid splash)
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbsr    DrawOneCell
        lbsr    DrawScores
        lda     HT
        cmpa    #2
        lbeq    pt_al
        cmpa    #0
        lbeq    pt_ms
        cmpa    #3
        lbeq    pt_sk
        leax    TMHit,pcr
        lbra    pt_msg
pt_ms   leax    TMMiss,pcr
        lbra    pt_msg
pt_sk   lbsr    MsgSunk
        lbsr    PauseLong
        lbsr    KeyFlush        ; Space fully up before computer / next input
        rts
pt_al   leax    TMAlr,pcr
        lbsr    ShowMsg
        lbsr    PauseMed
        lbsr    KeyFlush
        lbra    pt_i
pt_msg
        * X → HIT!/MISS!  — no Tone (PIA sound path freezes input)
        lbsr    ShowMsg
        lbsr    PauseMed
        lbsr    KeyFlush
        rts

ComputerTurn
        * Dramatic beat: announce, think, fire, result linger
        leax    TMComp,pcr
        lbsr    ShowMsg
        lbsr    PauseLong
        leax    TMCaim,pcr
        lbsr    ShowMsg
        lbsr    PauseMed
        lbsr    AiPick
        lda     AR
        beq     ct_fix
        cmpa    #10
        bls     ct_ar
ct_fix  lda     #1
        sta     AR
ct_ar   lda     AC
        beq     ct_fc
        cmpa    #10
        bls     ct_ac
ct_fc   lda     #1
        sta     AC
ct_ac
        lda     AR
        sta     TmpR
        lda     AC
        sta     TmpC
        clra
        lbsr    ApplyShot
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lda     AR
        sta     RR
        lda     AC
        sta     CC
        * flash target cell (solid, then result glyph)
        lbsr    CellOrigin
        lda     #$FF
        lbsr    CellFillA
        lbsr    PauseShort
        lbsr    DrawOneCell
        lbsr    PauseShort
        lbsr    CellOrigin
        lda     #$FF
        lbsr    CellFillA
        lbsr    PauseShort
        lbsr    DrawOneCell
        lbsr    DrawScores
        lda     HT
        beq     ct_m
        cmpa    #3
        beq     ct_s
        lda     #1
        sta     Hunt
        lda     AR
        sta     HR
        lda     AC
        sta     HC
        leax    TMCht,pcr
        lbsr    ShowMsg
        bra     ct_end
ct_m    leax    TMCms,pcr
        lbsr    ShowMsg
        bra     ct_end
ct_s    clr     Hunt
        lbsr    MsgSunk
ct_end  lbsr    PauseLong
        leax    TMComp2,pcr
        lbsr    ShowMsg
        lbsr    PauseMed
        lbsr    ClearMsg
        lbsr    KeyFlush
        rts

* Wipe full 8-pixel status band (y=180..187), then draw string at X.
* Old ClearMsg only erased 1 scanline → leftover glyphs looked messy.
ShowMsg
        pshs    x
        lbsr    ClearMsg
        puls    x
        lda     #8
        ldb     #180
        lbra    DrawStr

ClearMsg
        pshs    a,b,x
        lda     #180
        ldb     #GBPL
        mul
        tfr     d,x
        leax    GFX,x
        ldb     #8              ; 8 rows = one text line
cm_r    pshs    b
        ldb     #32             ; full width
        clra
cm_c    sta     ,x+
        decb
        bne     cm_c
        puls    b
        decb
        bne     cm_r
        puls    a,b,x
        rts

* Sunk banner: "SUNK " + craft name from SID (1..5)
MsgSunk
        pshs    a,b,x
        lbsr    ClearMsg
        leax    TMSunk,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        lda     SID
        cmpa    #1
        beq     msn1
        cmpa    #2
        beq     msn2
        cmpa    #3
        beq     msn3
        cmpa    #4
        beq     msn4
        leax    TNDest,pcr
        bra     msnx
msn1    leax    TNCarr,pcr
        bra     msnx
msn2    leax    TNBatt,pcr
        bra     msnx
msn3    leax    TNCrui,pcr
        bra     msnx
msn4    leax    TNSub,pcr
msnx    lda     #48             ; x after "SUNK " (8 + 5*8)
        ldb     #180
        lbsr    DrawStr
        puls    a,b,x
        rts

* Pauses (register counters only — never BSS)
* PauseShort ~0.25s, PauseMed ~0.9s, PauseLong ~1.8s @ 0.89MHz
PauseShort
        pshs    a,b,x
        ldb     #6
ps0     ldx     #$1400
ps1     leax    -1,x
        bne     ps1
        decb
        bne     ps0
        puls    a,b,x
        rts
PauseMed
        pshs    a,b,x
        ldb     #16
pm0     ldx     #$2000
pm1     leax    -1,x
        bne     pm1
        decb
        bne     pm0
        puls    a,b,x
        rts
PauseLong
        pshs    a,b,x
        ldb     #32
pl0     ldx     #$2400
pl1     leax    -1,x
        bne     pl1
        decb
        bne     pl0
        puls    a,b,x
        rts
PauseRead
        bra     PauseMed
TinyPause
        bra     PauseShort

DrawBattleHUD
        leax    TYou,pcr
        lda     #LX0
        ldb     #8
        lbsr    DrawStr
        leax    TRad,pcr
        lda     #RX0
        ldb     #8
        lbsr    DrawStr
        leax    TStat,pcr
        lda     #8
        ldb     #168
        lbsr    DrawStr
        rts

***********************************************************************
* ApplyShot A=grid(0 player /1 enemy) TmpR,TmpC → HT
***********************************************************************
ApplyShot
        sta     TmpG
        clr     HT
        clr     SID
        lda     TmpG
        lbne    ase
        ldx     #PS
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        cmpa    #6
        lbeq    asal
        cmpa    #7
        lbeq    asal
        tsta
        lbeq    aspm
        cmpa    #5
        lbhi    asx
        sta     SID
        lda     #7
        sta     ,x
        ldx     #AK
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #2
        sta     ,x
        dec     PH
        lda     #1
        sta     HT
        lbsr    CountShipPS
        lda     TmpCnt
        lbne    asx
        lda     #3
        sta     HT
        lbra    asx
aspm    lda     #6
        sta     ,x
        ldx     #AK
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #1
        sta     ,x
        clr     HT
        lbra    asx
ase     ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        lbne    asal
        ldx     #ES
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        tsta
        lbeq    asem
        cmpa    #5
        lbhi    asx
        sta     SID
        lda     #7
        sta     ,x
        ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #2
        sta     ,x
        * dec SR[SID-1]
        ldx     #SR
        lda     SID
        deca
        leax    a,x
        dec     ,x
        dec     EH
        lda     #1
        sta     HT
        lda     ,x
        lbne    asx
        lda     #3
        sta     HT
        lbra    asx
asem    ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #1
        sta     ,x
        clr     HT
        lbra    asx
asal    lda     #2
        sta     HT
asx     rts

CountShipPS
        clr     TmpCnt
        lda     #1
        sta     RR
csr     lda     #1
        sta     CC
csc     ldx     #PS
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        cmpa    SID
        bne     csn
        inc     TmpCnt
csn     inc     CC
        lda     CC
        cmpa    #11
        blo     csc
        inc     RR
        lda     RR
        cmpa    #11
        blo     csr
        rts

***********************************************************************
* AI: hunt after hit, else pseudo-random from Rnd, else scan.
* Try counter in B only (BSS Tries was unsafe).
***********************************************************************
AiPick
        lda     Hunt
        beq     ai_rnd
        lda     HR
        beq     ai_rnd
        lda     HR
        deca
        ldb     HC
        lbsr    ai_try
        lbcc    ai_got
        lda     HR
        inca
        ldb     HC
        lbsr    ai_try
        lbcc    ai_got
        lda     HR
        ldb     HC
        decb
        lbsr    ai_try
        lbcc    ai_got
        lda     HR
        ldb     HC
        incb
        lbsr    ai_try
        lbcc    ai_got
        clr     Hunt
ai_rnd  ldb     #40             ; max random tries (register!)
ai_rl   pshs    b
        lbsr    Rand
        anda    #$0F
        beq     ai_rz
        cmpa    #10
        bls     ai_r1
ai_rz   lda     #1
ai_r1   sta     AR
        lbsr    Rand
        anda    #$0F
        beq     ai_cz
        cmpa    #10
        bls     ai_c1
ai_cz   lda     #5
ai_c1   sta     AC
        ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        puls    b
        beq     ai_got          ; empty cell — AR/AC set
        decb
        bne     ai_rl
ai_scan lda     #1
        sta     AR
ais_r   lda     #1
        sta     AC
ais_c   ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        beq     ai_got
        inc     AC
        lda     AC
        cmpa    #11
        blo     ais_c
        inc     AR
        lda     AR
        cmpa    #11
        blo     ais_r
        lda     #1
        sta     AR
        sta     AC
ai_got  rts

ai_try
        tsta
        beq     ait_bad
        cmpa    #10
        bhi     ait_bad
        tstb
        beq     ait_bad
        cmpb    #10
        bhi     ait_bad
        pshs    a,b
        sta     RR
        stb     CC
        ldx     #AK
        lbsr    CellAddr
        lda     ,x
        bne     ait_b2
        puls    a,b
        sta     AR
        stb     AC
        andcc   #$FE
        rts
ait_b2  puls    a,b
ait_bad orcc    #$01
        rts

***********************************************************************
* Game over — boards stay; result text ABOVE them (y=0..23 only).
* Never draw at y=80 (that is through the grids).
***********************************************************************
GameOver
        lbsr    DrawBattle
        * wipe rows 0..23 (everything above LY0 boards) + solid bar
        lbsr    ClearTopBanner
        * double-height feel: two text rows in the free banner
        lda     EH
        bne     gol
        leax    TWin,pcr
        bra     gow
gol     leax    TLose,pcr
gow     lda     #72
        ldb     #2
        lbsr    DrawStr
        leax    TGo,pcr
        lda     #40
        ldb     #12
        lbsr    DrawStr
        lbsr    PauseLong
        lbsr    PauseLong
        lbsr    WaitKey
        rts

* Clear scanlines 0..23 (strictly above board LY0=24)
ClearTopBanner
        pshs    a,b,x
        ldx     #GFX
        ldb     #24
ctb_r   pshs    b
        ldb     #32
        clra
ctb_c   sta     ,x+
        decb
        bne     ctb_c
        puls    b
        decb
        bne     ctb_r
        puls    a,b,x
        rts

***********************************************************************
* Draw PMODE 4 dual boards — ALL cell graphics are byte stores (fast).
* Empty cell = hollow box so the 10x10 grid is always visible.
* Cursor = XOR invert of cell (toggle twice = restore).
***********************************************************************
DrawBoardsOnly
        lbsr    GfxCls
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lbsr    DrawOneBoard
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lbsr    DrawOneBoard
        rts

DrawBattle
        lbsr    DrawBoardsOnly
        lbsr    DrawBattleHUD
        lbsr    DrawScores
        rts

DrawScores
        * wipe score strip (y=168..175) so shorter numbers leave no trails
        pshs    a,b,x
        lda     #168
        ldb     #GBPL
        mul
        tfr     d,x
        leax    GFX,x
        ldb     #8
dsc_r   pshs    b
        ldb     #32
        clra
dsc_c   sta     ,x+
        decb
        bne     dsc_c
        puls    b
        decb
        bne     dsc_r
        puls    a,b,x
        leax    TScE,pcr
        lda     #8
        ldb     #168
        lbsr    DrawStr
        lda     EH
        lbsr    DrawNum
        leax    TScY,pcr
        lbsr    DrawStrCont
        lda     PH
        lbsr    DrawNum
        rts

DrawOneBoard
        lda     #1
        sta     RR
dob_r   lda     #1
        sta     CC
dob_c   lbsr    DrawOneCell
        inc     CC
        lda     CC
        cmpa    #11
        blo     dob_c
        inc     RR
        lda     RR
        cmpa    #11
        blo     dob_r
        rts

* BoardWhich, BX0, BY0, RR, CC
DrawOneCell
        pshs    a,b,x
        lbsr    CellGlyph
        sta     GType
        lbsr    CellOrigin      ; → X0,Y0 from RR,CC,BX0,BY0
        lbsr    DrawCell
        puls    a,b,x
        rts

* RR,CC,BX0,BY0 → X0,Y0 (preserves RR/CC)
CellOrigin
        pshs    a,b
        lda     CC
        deca
        ldb     #CELL
        mul
        addb    BX0
        stb     X0
        lda     RR
        deca
        ldb     #CELL
        mul
        addb    BY0
        stb     Y0
        puls    a,b
        rts

* CellVal = raw grid byte; GType = 0 empty 1 ship 2 miss 3 hit
CellGlyph
        lda     BoardWhich
        bne     cg_r
        ldx     #PS
        bra     cg_g
cg_r    ldx     #RD
cg_g    lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        sta     CellVal
        tsta
        beq     cg0
        lda     BoardWhich
        bne     cg_rad
        lda     CellVal
        cmpa    #6
        beq     cg2
        cmpa    #7
        beq     cg3
        lda     #1
        rts
cg_rad  lda     CellVal
        cmpa    #1
        beq     cg2
        lda     #3
        rts
cg0     clra
        rts
cg2     lda     #2
        rts
cg3     lda     #3
        rts

* DrawCell using 8-byte patterns (ships look like mini hulls, not solid bars)
DrawCell
        lda     GType
        beq     dc_pat_e
        cmpa    #2
        beq     dc_pat_m
        cmpa    #3
        beq     dc_pat_h
        * ship id 1..5 → pattern
        lda     CellVal
        beq     dc_s1
        cmpa    #5
        bls     dc_sok
        lda     #1
dc_sok  deca
        ldb     #8
        mul
        leax    PatShip,pcr
        leax    d,x
        bra     CellBlit
dc_s1   leax    PatShip,pcr
        bra     CellBlit
dc_pat_m
        leax    PatMiss,pcr
        bra     CellBlit
dc_pat_h
        leax    PatHit,pcr
        bra     CellBlit
dc_pat_e
        leax    PatEmpty,pcr
* X → 8 row bytes; blit to X0,Y0
CellBlit
        pshs    x
        lbsr    CellAddrByte
        tfr     x,y             ; Y = screen
        puls    x               ; X = pattern
        ldb     #8
cbl     lda     ,x+
        sta     ,y
        lda     #GBPL
        leay    a,y
        decb
        bne     cbl
        rts

* Solid fill for cursor (A = fill byte)
CellFillA
        sta     TmpB
        lbsr    CellAddrByte
        ldb     #8
        lda     TmpB
cfa1    sta     ,x
        pshs    a,b
        lda     #GBPL
        leax    a,x
        puls    a,b
        decb
        bne     cfa1
        rts

* Empty = hollow box. Miss = open ring. Hit = bold X (must not look alike).
PatEmpty
        fcb     $FF,$81,$81,$81,$81,$81,$81,$FF
PatMiss
        fcb     $00,$3C,$66,$42,$42,$66,$3C,$00  * open O / splash
PatHit
        fcb     $C3,$E7,$7E,$3C,$3C,$7E,$E7,$C3  * bold X
PatGhost
        fcb     $AA,$55,$AA,$55,$AA,$55,$AA,$55  * placement preview
PatShip
        fcb     $00,$3C,$7E,$FF,$FF,$7E,$3C,$18  * 1 carrier
        fcb     $00,$18,$3C,$7E,$FF,$7E,$3C,$18  * 2 battleship
        fcb     $00,$00,$3C,$7E,$7E,$3C,$00,$00  * 3 cruiser
        fcb     $00,$18,$3C,$7E,$3C,$18,$00,$00  * 4 sub
        fcb     $00,$00,$7E,$FF,$FF,$7E,$00,$00  * 5 destroyer

* X0,Y0 → X = &GFX + Y*32 + X/8
CellAddrByte
        pshs    a,b
        lda     Y0
        ldb     #GBPL
        mul
        tfr     d,x
        lda     X0
        lsra
        lsra
        lsra
        leax    a,x
        leax    GFX,x
        puls    a,b
        rts

UndrawCursorLeft
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbra    DrawOneCell

UndrawCursorRight
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbra    DrawOneCell

DrawCursorLeft
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        bra     DrawCur
DrawCursorRight
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
DrawCur
        * Solid cursor block (no XOR state). Undraw restores via DrawOneCell.
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbsr    CellOrigin
        lda     #$FF
        lbra    CellFillA

***********************************************************************
* Low-level PMODE 4 graphics
***********************************************************************
GfxCls
        ldx     #GFX
        ldy     #6144/2
        clra
        clrb
gc1     std     ,x++
        leay    -1,y
        bne     gc1
        rts

* Plot2: set pixel A=X (0-255), B=Y (0-191)
* Preserves X (DrawChar walks font data in X across Plot2 calls).
Plot2
        cmpb    #192
        bhs     p2x
        pshs    a,b,x
        sta     PixX
        stb     PixY
        lda     PixY
        ldb     #GBPL
        mul                     ; D = Y*32
        tfr     d,x
        lda     PixX
        lsra
        lsra
        lsra                    ; X/8
        leax    a,x
        leax    GFX,x
        lda     PixX
        anda    #7
        sta     TmpI
        lda     #$80
p2sh    tst     TmpI
        beq     p2or
        lsra
        dec     TmpI
        bra     p2sh
p2or    tfr     a,b
        orb     ,x
        stb     ,x
        puls    a,b,x
p2x     rts

FillRect2
        lda     Ht
        beq     fr2x
        sta     TY
        lda     RY
        sta     PY
fr2y    lda     Wd
        beq     fr2x
        sta     TX
        lda     RX
        sta     PX
fr2x1   lda     PX
        ldb     PY
        lbsr    Plot2
        inc     PX
        dec     TX
        bne     fr2x1
        inc     PY
        dec     TY
        bne     fr2y
fr2x    rts

DrawRect
        lda     Wd
        beq     drx
        lda     Ht
        beq     drx
        lda     RX
        sta     PX
        lda     Wd
        sta     TX
drtb    lda     PX
        ldb     RY
        lbsr    Plot2
        lda     PX
        ldb     RY
        addb    Ht
        decb
        lbsr    Plot2
        inc     PX
        dec     TX
        bne     drtb
        lda     RY
        sta     PY
        lda     Ht
        sta     TY
drsd    lda     RX
        ldb     PY
        lbsr    Plot2
        lda     RX
        adda    Wd
        deca
        ldb     PY
        lbsr    Plot2
        inc     PY
        dec     TY
        bne     drsd
drx     rts

***********************************************************************
* Text — 8x8 glyphs pre-defined; each char = 8 byte stores (not Plot2)
***********************************************************************
DrawStr
        sta     TX
        stb     TY
DrawStrCont
ds1     lda     ,x+
        beq     dsx
        sta     TmpCh
        pshs    x
        lda     TX
        ldb     TY
        lbsr    DrawChar
        puls    x
        lda     TX
        adda    #8
        sta     TX
        bra     ds1
dsx     rts

DrawNum
        clr     TmpH
dn1     cmpa    #10
        blo     dn2
        suba    #10
        inc     TmpH
        bra     dn1
dn2     pshs    a
        lda     TmpH
        adda    #'0
        sta     TmpCh
        lda     TX
        ldb     TY
        lbsr    DrawChar
        lda     TX
        adda    #8
        sta     TX
        puls    a
        adda    #'0
        sta     TmpCh
        lda     TX
        ldb     TY
        lbsr    DrawChar
        lda     TX
        adda    #8
        sta     TX
        rts

* A=x (use multiple of 8), B=y, TmpCh=ASCII
DrawChar
        sta     CX
        stb     CY
        lda     TmpCh
        cmpa    #'a
        blo     dcu
        cmpa    #'z
        bhi     dcu
        suba    #32
dcu     cmpa    #32
        blo     dcx
        cmpa    #91
        bhs     dcx
        suba    #32
        ldb     #8
        mul
        ldx     #Font8
        leax    d,x
        lda     CY
        ldb     #GBPL
        mul
        tfr     d,y
        lda     CX
        lsra
        lsra
        lsra
        leay    a,y
        leay    GFX,y
        ldb     #8
dc_blit lda     ,x+
        sta     ,y
        lda     #GBPL
        leay    a,y
        decb
        bne     dc_blit
dcx     rts

* 8x8 font ASCII 32-90, row-major, bit7=left. 8 bytes/glyph — blit as 8 STA.
Font8
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * space
        fcb     $18,$18,$18,$18,$18,$00,$18,$18  * !
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * "
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * #
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * $
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * %
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * &
        fcb     $18,$18,$10,$00,$00,$00,$00,$00  * '
        fcb     $0C,$18,$30,$30,$30,$18,$0C,$00  * (
        fcb     $30,$18,$0C,$0C,$0C,$18,$30,$00  * )
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * *
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * +
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * ,
        fcb     $00,$00,$00,$7E,$00,$00,$00,$00  * -
        fcb     $00,$00,$00,$00,$00,$00,$18,$18  * .
        fcb     $03,$06,$0C,$18,$30,$60,$C0,$00  * /
        * slashed zero — oval + thin diagonal; no extra right-edge bits
        fcb     $3C,$66,$C3,$D3,$CB,$C3,$66,$3C  * 0
        fcb     $18,$38,$78,$18,$18,$18,$18,$7E  * 1
        fcb     $7E,$C3,$03,$06,$0C,$18,$30,$FF  * 2
        fcb     $7E,$C3,$03,$1E,$03,$03,$C3,$7E  * 3
        fcb     $0C,$1C,$3C,$6C,$CC,$FF,$0C,$0C  * 4
        fcb     $FF,$C0,$C0,$7E,$03,$03,$C3,$7E  * 5
        fcb     $3C,$60,$C0,$7E,$C3,$C3,$C3,$7E  * 6
        fcb     $FF,$03,$06,$0C,$18,$30,$30,$30  * 7
        fcb     $7E,$C3,$C3,$7E,$C3,$C3,$C3,$7E  * 8
        fcb     $7E,$C3,$C3,$7F,$03,$03,$06,$7C  * 9
        fcb     $00,$18,$18,$00,$00,$18,$18,$00  * :
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * ;
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * <
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * =
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * >
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * ?
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * @
        fcb     $3C,$66,$C3,$C3,$FF,$C3,$C3,$C3  * A
        fcb     $FE,$C3,$C3,$FE,$C3,$C3,$C3,$FE  * B
        fcb     $7E,$C3,$C0,$C0,$C0,$C0,$C3,$7E  * C
        fcb     $FC,$C6,$C3,$C3,$C3,$C3,$C6,$FC  * D
        fcb     $FF,$C0,$C0,$FC,$C0,$C0,$C0,$FF  * E
        fcb     $FF,$C0,$C0,$FC,$C0,$C0,$C0,$C0  * F
        fcb     $7E,$C3,$C0,$C0,$CF,$C3,$C3,$7E  * G
        fcb     $C3,$C3,$C3,$FF,$C3,$C3,$C3,$C3  * H
        fcb     $7E,$18,$18,$18,$18,$18,$18,$7E  * I
        fcb     $03,$03,$03,$03,$03,$C3,$C3,$7E  * J
        fcb     $C3,$C6,$CC,$F0,$CC,$C6,$C3,$C3  * K
        fcb     $C0,$C0,$C0,$C0,$C0,$C0,$C0,$FF  * L
        fcb     $C3,$E7,$FF,$DB,$C3,$C3,$C3,$C3  * M
        fcb     $C3,$E3,$F3,$DB,$CF,$C7,$C3,$C3  * N
        fcb     $7E,$C3,$C3,$C3,$C3,$C3,$C3,$7E  * O
        fcb     $FE,$C3,$C3,$FE,$C0,$C0,$C0,$C0  * P
        fcb     $7E,$C3,$C3,$C3,$DB,$CF,$C6,$7D  * Q
        fcb     $FE,$C3,$C3,$FE,$CC,$C6,$C3,$C3  * R
        fcb     $7E,$C3,$C0,$7E,$03,$03,$C3,$7E  * S
        fcb     $FF,$18,$18,$18,$18,$18,$18,$18  * T
        fcb     $C3,$C3,$C3,$C3,$C3,$C3,$C3,$7E  * U
        fcb     $C3,$C3,$C3,$C3,$C3,$66,$3C,$18  * V
        fcb     $C3,$C3,$C3,$C3,$DB,$FF,$E7,$C3  * W
        fcb     $C3,$C3,$66,$3C,$3C,$66,$C3,$C3  * X
        fcb     $C3,$C3,$66,$3C,$18,$18,$18,$18  * Y
        fcb     $FF,$03,$06,$0C,$18,$30,$60,$FF  * Z

***********************************************************************
* Keyboard — POLCAT with true key-up (bounded). Fixed auto-refire freeze:
* old WaitKey only "drained" ~80 polls, so Space still held re-fired the
* same cell after MISS (ALREADY loop looked like a hang).
***********************************************************************
POLCAT  equ     $A000

* Wait until no key (or timeout). Register counters only.
KeyFlush
        pshs    a,b,x
        andcc   #$EF
        ldx     #$3000
kf1     jsr     [POLCAT]
        anda    #$7F
        beq     kf2
        leax    -1,x
        bne     kf1
kf2     * brief settle
        ldb     #0
kf3     decb
        bne     kf3
        puls    a,b,x
        rts

WaitKey
        andcc   #$EF            ; IRQs on for keyboard scan
        lbsr    Rand            ; entropy each wait
        * ensure previous key is fully up first
        lbsr    KeyFlush
        * wait for key; bump Rnd every poll (title timing → variety)
wk_wt   inc     Rnd
        jsr     [POLCAT]
        anda    #$7F
        beq     wk_wt
        sta     KChar
        * wait for key UP (timeout — never hang forever)
        ldx     #$6000
wk_up   jsr     [POLCAT]
        anda    #$7F
        beq     wk_up0
        leax    -1,x
        bne     wk_up
wk_up0  * small settle
        ldb     #0
wk_st   decb
        bne     wk_st
        lbsr    Rand
        lda     KChar
        anda    #$7F
        cmpa    #'a
        blo     wk_done
        cmpa    #'z
        bhi     wk_done
        suba    #32
wk_done rts

* Stored next to code so it is always in the LOADM image
KChar   fcb     0


* Sound / RNG
* HARD NO-OP. Any write to $FF01/$FF03 (keyboard PIA) during combat has
* frozen input after the first shot on XRoar, even with save/restore.
* Splash/title do not need sound. Revisit only with a DAC-only routine
* that never touches PIA0, tested after hit/miss specifically.
***********************************************************************
SoundInit
        rts

Tone
Beep
Click
        rts

SeedRnd
        * Prefer BASIC TIMER; fall back. WaitKey further mixes Rnd.
        lda     $0112
        eora    $0113
        eora    $FF03
        bne     srok
        lda     #$A5
srok    eora    #$5A
        tsta
        bne     srok2
        lda     #$C3
srok2   sta     Rnd
        lbsr    Rand
        lbsr    Rand
        rts
Rand
        lda     Rnd
        bne     rnz
        lda     #$A5
rnz     lsra
        bcc     rok
        eora    #$B4
rok     tsta
        bne     rok2
        lda     #1
rok2    sta     Rnd
        rts
RandN
        sta     TmpN
        beq     rn1
rn0     lbsr    Rand
        lda     Rnd
rnm     cmpa    TmpN
        blo     rno
        suba    TmpN
        bra     rnm
rno     inca
        rts
rn1     lda     #1
        rts

* Strings
***********************************************************************
TTitle  fcn     "SEA BATTLE"
TSub    fcn     "DUAL BOARD DUEL"
TCtrl   fcn     "WASD MOVE  R ROTATE"
TCtrl2  fcn     "SPACE PUT  P AUTO"
TGo     fcn     "PRESS ANY KEY"
TCopy   fcn     "(C) ALEX GAYER 2026"
TPlace  fcn     "PLACE FLEET"
TShip   fcn     "SHIP"
THV     fcn     ""
TH      fcn     "HORIZ"
TV      fcn     "VERT"
THint   fcn     "WASD MOVE  R ROT  SPC  P"
TReady  fcn     "READY - KEY"
TComp   fcn     "COMPUTER PLACES..."
TYou    fcn     "YOUR FLEET"
TRad    fcn     "RADAR"
TStat   fcn     ""
TScE    fcn     "E:"
TScY    fcn     " Y:"
TMHit   fcn     "HIT!"
TMMiss  fcn     "MISS!"
TMSunk  fcn     "SUNK "
TMAlr   fcn     "ALREADY"
TMComp  fcn     "COMPUTER'S TURN"
TMCaim  fcn     "AIMING..."
TMCht   fcn     "YOU'RE HIT!"
TMCms   fcn     "COMPUTER MISSES"
TMComp2 fcn     "COMPUTER DONE"
TWin    fcn     "YOU WIN!"
TLose   fcn     "YOU LOSE"
TNCarr  fcn     "CARRIER"
TNBatt  fcn     "BATTLESHIP"
TNCrui  fcn     "CRUISER"
TNSub   fcn     "SUB"
TNDest  fcn     "DESTROYER"
TI0     fcn     "HOW TO PLAY"
TI1     fcn     "WASD  MOVE SHIP"
TI2     fcn     "SPACE PLACE / FIRE"
TI3     fcn     "R     ROTATE SHIP"
TI4     fcn     "P     AUTO-PLACE"
TI5     fcn     "LEFT  YOUR FLEET"
TI6     fcn     "RIGHT ENEMY RADAR"
TI7     fcn     "SINK ALL 17 HITS"
TI8     fcn     "O  MISS    X  HIT"
TI9     fcn     "STATUS LINE BELOW"
TmpCh   zmb     1
TmpTone zmb     1

***********************************************************************
* Variables (in LOADM image)
* (Title splash is separate NAVAL.BIN → $0E00, not embedded here.)
***********************************************************************
PS      zmb     100
ES      zmb     100
RD      zmb     100
AK      zmb     100
SL      zmb     5
SR      zmb     5
PH      zmb     1
EH      zmb     1
Hunt    zmb     1
HR      zmb     1
HC      zmb     1
AR      zmb     1
AC      zmb     1
CurR    zmb     1
CurC    zmb     1
Horiz   zmb     1
ShipId  zmb     1
PlaceGrid zmb   1
Tries   zmb     1
TmpG    zmb     1
TmpR    zmb     1
TmpC    zmb     1
TmpL    zmb     1
TmpI    zmb     1
TmpN    zmb     1
TmpH    zmb     1
TmpCnt  zmb     1
TmpB    zmb     1
RR      zmb     1
CC      zmb     1
Rnd     zmb     1
BoardWhich zmb  1
BX0     zmb     1
BY0     zmb     1
X0      zmb     1
Y0      zmb     1
RX      zmb     1
RY      zmb     1
Wd      zmb     1
Ht      zmb     1
GType   zmb     1
CellVal zmb     1
PixX    zmb     1
PixY    zmb     1
PX      zmb     1
PY      zmb     1
TX      zmb     1
TY      zmb     1
CX      zmb     1
CY      zmb     1
ColMask zmb     1
ColN    zmb     1
RowBits zmb     1
RowN    zmb     1
HT      zmb     1
SID     zmb     1
CP      zmb     1

        end     START
