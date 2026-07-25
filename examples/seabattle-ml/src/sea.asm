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
* Title (bitmap)
***********************************************************************
TitleScreen
        lbsr    GfxCls
        leax    TTitle,pcr
        lda     #40
        ldb     #40
        lbsr    DrawStr
        leax    TSub,pcr
        lda     #28
        ldb     #60
        lbsr    DrawStr
        leax    TCtrl,pcr
        lda     #8
        ldb     #100
        lbsr    DrawStr
        leax    TCtrl2,pcr
        lda     #8
        ldb     #112
        lbsr    DrawStr
        leax    TGo,pcr
        lda     #40
        ldb     #150
        lbsr    DrawStr
        lbsr    WaitKey
        rts

***********************************************************************
* Placement
***********************************************************************
PlacePlayerFleet
        lda     #1
        sta     ShipId
        clr     Horiz           ; 0=vert 1=horiz
pp_loop
        lda     ShipId
        cmpa    #6
        lbhs    pp_done
pp_draw
        lbsr    DrawBoardsOnly  ; no battle labels (avoids overlap)
        lbsr    DrawPlaceHUD
        lbsr    DrawScores
        lbsr    DrawCursorLeft
pp_in
        lbsr    WaitKey         ; A=0 if none (ignore)
        tsta
        lbeq    pp_in
        cmpa    #'A
        lbeq    pp_auto
        cmpa    #'a
        lbeq    pp_auto
        cmpa    #'R
        lbeq    pp_rot
        cmpa    #'r
        lbeq    pp_rot
        cmpa    #9
        lbeq    pp_r
        cmpa    #'D
        lbeq    pp_r
        cmpa    #'d
        lbeq    pp_r
        cmpa    #'L
        lbeq    pp_r
        cmpa    #'l
        lbeq    pp_r
        cmpa    #8
        lbeq    pp_l
        cmpa    #'J
        lbeq    pp_l
        cmpa    #'j
        lbeq    pp_l
        cmpa    #'S
        lbeq    pp_dn
        cmpa    #'s
        lbeq    pp_dn
        cmpa    #10
        lbeq    pp_dn
        cmpa    #'W
        lbeq    pp_u
        cmpa    #'w
        lbeq    pp_u
        cmpa    #32
        lbeq    pp_put
        cmpa    #13
        lbeq    pp_put
        lbra    pp_in
pp_rot
        lda     Horiz
        eora    #1
        sta     Horiz
        lbra    pp_draw
pp_r    lda     CurC
        cmpa    #10
        lbhs    pp_in
        lbsr    UndrawCursorLeft
        inc     CurC
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_l    lda     CurC
        cmpa    #1
        lbls    pp_in
        lbsr    UndrawCursorLeft
        dec     CurC
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_dn   lda     CurR
        cmpa    #10
        lbhs    pp_in
        lbsr    UndrawCursorLeft
        inc     CurR
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_u    lda     CurR
        cmpa    #1
        lbls    pp_in
        lbsr    UndrawCursorLeft
        dec     CurR
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_put
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        clr     TmpG
        ldb     ShipId
        ldx     #SL-1
        abx
        ldb     ,x
        stb     TmpL
        lbsr    CanPlace
        lda     CP
        lbeq    pp_bad
        lda     #0
        ldb     ShipId
        lbsr    PlaceShip
        inc     ShipId
        lda     #1
        lbsr    Beep
        lbra    pp_loop
pp_bad
        lda     #0
        lbsr    Beep
        lbra    pp_in
pp_auto
        lda     #0
        lbsr    AutoPlaceFleet
        lda     #6
        sta     ShipId
        lda     #1
        lbsr    Beep
pp_done
        lbsr    DrawBoardsOnly
        * skip slow DrawStr banner — one short beep means ready
        lbsr    WaitKey
        rts

DrawPlaceHUD
        * top banner only (y=2..16) — not over boards at y=24
        leax    TPlace,pcr
        lda     #8
        ldb     #2
        lbsr    DrawStr
        leax    THint,pcr
        lda     #8
        ldb     #12
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
* Auto place A=grid
***********************************************************************
AutoPlaceFleet
        sta     PlaceGrid
        lda     #1
        sta     ShipId
ap_s    lda     ShipId
        cmpa    #6
        lbhs    ap_x
        clr     Tries
ap_t    inc     Tries
        lda     Tries
        cmpa    #250
        bhi     ap_n
        lbsr    Rand
        anda    #1
        sta     Horiz
        ldb     ShipId
        ldx     #SL-1
        abx
        ldb     ,x
        stb     TmpL
        lda     Horiz
        bne     ap_hh
        lda     #11
        suba    TmpL
        lbsr    RandN
        sta     TmpR
        lda     #10
        lbsr    RandN
        sta     TmpC
        bra     ap_c
ap_hh   lda     #10
        lbsr    RandN
        sta     TmpR
        lda     #11
        suba    TmpL
        lbsr    RandN
        sta     TmpC
ap_c    lda     PlaceGrid
        sta     TmpG
        lbsr    CanPlace
        lda     CP
        beq     ap_t
        lda     PlaceGrid
        ldb     ShipId
        lbsr    PlaceShip
ap_n    inc     ShipId
        bra     ap_s
ap_x    rts

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
        ldx     #SL-1
        abx
        ldb     ,x
        stb     TmpL
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
        lbsr    DrawCursorRight
        lbra    pt_i
pt_l    lda     CurC
        cmpa    #1
        lbls    pt_i
        lbsr    UndrawCursorRight
        dec     CurC
        lbsr    DrawCursorRight
        lbra    pt_i
pt_dn   lda     CurR
        cmpa    #10
        lbhs    pt_i
        lbsr    UndrawCursorRight
        inc     CurR
        lbsr    DrawCursorRight
        lbra    pt_i
pt_up   lda     CurR
        cmpa    #1
        lbls    pt_i
        lbsr    UndrawCursorRight
        dec     CurR
        lbsr    DrawCursorRight
        lbra    pt_i
pt_fire
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        lda     #1
        lbsr    ApplyShot
        * refresh only the shot cell on radar (fast)
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
        lbsr    DrawCursorRight
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
pt_sk   leax    TMSunk,pcr
        lbra    pt_msg
pt_al   leax    TMAlr,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        lda     #0
        lbsr    Beep
        lbsr    WaitKey
        lbra    pt_i
pt_msg  lda     #8
        ldb     #180
        lbsr    DrawStr
        lda     HT
        beq     pt_b0
        cmpa    #3
        beq     pt_b2
        lda     #1
        bra     pt_bb
pt_b0   clra
        bra     pt_bb
pt_b2   lda     #2
pt_bb   lbsr    Beep
        lbsr    WaitKey
        rts

ComputerTurn
        leax    TMComp,pcr
        lda     #80
        ldb     #180
        lbsr    DrawStr
        lbsr    AiPick
        lda     AR
        sta     TmpR
        lda     AC
        sta     TmpC
        clra
        lbsr    ApplyShot
        * refresh only the hit cell on player fleet
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
        lbsr    DrawOneCell
        lbsr    DrawScores
        leax    TMComp2,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
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
        lda     #1
        bra     ct_b
ct_m    clra
        bra     ct_b
ct_s    clr     Hunt
        lda     #2
ct_b    lbsr    Beep
        lbsr    WaitKey
        rts

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
        ldx     #SR-1
        ldb     SID
        abx
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
* AI
***********************************************************************
AiPick
        lda     Hunt
        lbeq    air
        lda     #1
        sta     TmpI
ain     lda     TmpI
        cmpa    #5
        lbhs    air0
        lda     HR
        ldb     HC
        lda     TmpI
        cmpa    #1
        lbne    ad2
        lda     HR
        deca
        ldb     HC
        lbra    ait
ad2     cmpa    #2
        lbne    ad3
        lda     HR
        inca
        ldb     HC
        lbra    ait
ad3     cmpa    #3
        lbne    ad4
        lda     HR
        ldb     HC
        decb
        lbra    ait
ad4     lda     HR
        ldb     HC
        incb
ait     tsta
        lbeq    aix
        cmpa    #10
        lbhi    aix
        tstb
        lbeq    aix
        cmpb    #10
        lbhi    aix
        sta     RR
        stb     CC
        ldx     #AK
        lbsr    CellAddr
        lda     ,x
        lbne    aix
        lda     RR
        sta     AR
        lda     CC
        sta     AC
        rts
aix     inc     TmpI
        lbra    ain
air0    clr     Hunt
air     clr     Tries
ail     inc     Tries
        lda     Tries
        cmpa    #200
        lbhi    aisc
        lda     #10
        lbsr    RandN
        sta     AR
        lda     #10
        lbsr    RandN
        sta     AC
        ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        lbne    ail
        rts
aisc    lda     #1
        sta     AR
aisr    lda     #1
        sta     AC
aisc2   ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        lbeq    aiso
        inc     AC
        lda     AC
        cmpa    #11
        blo     aisc2
        inc     AR
        lda     AR
        cmpa    #11
        blo     aisr
        lda     #1
        sta     AR
        sta     AC
aiso    rts

***********************************************************************
* Game over
***********************************************************************
GameOver
        lbsr    DrawBattle
        lda     EH
        bne     gol
        leax    TWin,pcr
        bra     gow
gol     leax    TLose,pcr
gow     lda     #80
        ldb     #100
        lbsr    DrawStr
        lbsr    WaitKey
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
        tsta
        beq     cg0
        lda     BoardWhich
        bne     cg_rad
        * fleet: 1-5 ship, 6 miss, 7 hit
        lda     ,x
        cmpa    #6
        beq     cg2
        cmpa    #7
        beq     cg3
        lda     #1
        rts
cg_rad  * radar: 1 miss, 2 hit
        lda     ,x
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

* DrawCell: GType + X0,Y0. X0 multiple of 8, CELL=8.
* 0 empty hollow  1 ship solid  2 miss  3 hit solid
DrawCell
        lda     GType
        beq     dc_emp
        cmpa    #2
        beq     dc_miss
        lda     #$FF            ; solid
        lbra    CellFillA
dc_miss lda     #$00
        lbsr    CellFillA
        * center blot
        lda     Y0
        adda    #3
        ldb     #GBPL
        mul
        tfr     d,x
        lda     X0
        lsra
        lsra
        lsra
        leax    a,x
        leax    GFX,x
        lda     #$3C
        sta     ,x
        lda     GBPL
        leax    a,x
        lda     #$3C
        sta     ,x
        rts
dc_emp
        * hollow box: top/bottom $FF, sides $81
        lbsr    CellAddrByte    ; X → first byte of cell
        lda     #$FF
        sta     ,x
        ldb     #6
        lda     #GBPL
dce1    leax    a,x
        pshs    a
        lda     #$81
        sta     ,x
        puls    a
        decb
        bne     dce1
        lda     #GBPL
        leax    a,x
        lda     #$FF
        sta     ,x
        rts

* Fill 8 rows at X0,Y0 with byte in A
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
        * XOR invert cell under cursor (fast, no Plot2)
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbsr    CellOrigin
        lbsr    CellAddrByte
        ldb     #8
dcur1   lda     ,x
        eora    #$FF
        sta     ,x
        lda     #GBPL
        leax    a,x
        decb
        bne     dcur1
        rts

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
* Text
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
        adda    #6
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
        adda    #6
        sta     TX
        puls    a
        adda    #'0
        sta     TmpCh
        lda     TX
        ldb     TY
        lbsr    DrawChar
        lda     TX
        adda    #6
        sta     TX
        rts

* 5x7 font, column-major, bit0=TOP of column (bit1 = next row down, …).
* Index = ASCII-32, glyphs 32..90 only.
DrawChar
        sta     CX
        stb     CY
        lda     TmpCh
        cmpa    #'a
        blo     dcup
        cmpa    #'z
        bhi     dcup
        suba    #32             ; a-z → A-Z
dcup    cmpa    #32
        blo     dcz
        cmpa    #91             ; reject >= '['
        bhs     dcz
        suba    #32             ; 0..58
        ldb     #5
        mul                     ; D = glyph offset
        ldx     #Font
        leax    d,x             ; X → 5 column bytes
        lda     #5
        sta     TmpL
dc_col  lda     ,x+
        sta     TmpB
        lda     #7              ; rows: bit0 .. bit6
        sta     TmpI
        lda     CY
        sta     PY
dc_row  lda     TmpB
        bita    #$01            ; LSB = top of glyph
        beq     dc_s
        lda     CX
        ldb     PY
        lbsr    Plot2
dc_s    lsr     TmpB            ; next row down
        inc     PY
        dec     TmpI
        bne     dc_row
        inc     CX
        dec     TmpL
        bne     dc_col
dcz     rts

***********************************************************************
* Matrix keyboard — edge triggered (release → press → release).
* Never invents Space on timeout (that was firing bogus game actions).
* Returns A=ASCII, or A=0 if idle timeout (caller should ignore).
*
* Also tries ROM POLCAT as a second source (works on some XRoar setups).
***********************************************************************
POLCAT  equ     $A000

WaitKey
        * Loop until a real key is received (never fake Space).
        * 1) wait for release  2) wait for press  3) decode  4) wait release
wk_start
        lbsr    KeyWaitUp
wk_wait_dn
        lbsr    KeyAny
        tsta
        bne     wk_got
        jsr     [POLCAT]
        tsta
        beq     wk_wait_dn
        * ROM path
        pshs    a
        lbsr    KeyWaitUp
        puls    a
        cmpa    #'a
        blo     wk_rok
        cmpa    #'z
        bhi     wk_rok
        suba    #32
wk_rok  tsta
        beq     wk_start
        rts
wk_got
        ldx     #$C0            ; debounce
wk_db   leax    -1,x
        bne     wk_db
        lbsr    KeyDecode
        pshs    a
        lbsr    KeyWaitUp
        puls    a
        tsta
        beq     wk_start
        rts

* Wait until no keys (bounded)
KeyWaitUp
        ldb     #$28
        ldx     #0
kwu1    lbsr    KeyAny
        tsta
        beq     kwu2
        leax    -1,x
        bne     kwu1
        decb
        bne     kwu1
kwu2    lda     #$FF
        sta     PIA0D           ; idle columns high
        rts

* A=0 none, A!=0 some key down. Restores columns to $FF.
KeyAny
        pshs    b,x
        clr     ColN
ka1     leax    ColTab,pcr
        lda     ColN
        lda     a,x
        sta     PIA0D
        lda     PIA0
        anda    #$7F
        cmpa    #$7F
        bne     ka_yes
        inc     ColN
        lda     ColN
        cmpa    #7              ; 7 columns used on CoCo
        blo     ka1
        clra
        bra     ka_out
ka_yes  lda     #1
ka_out  pshs    a
        lda     #$FF
        sta     PIA0D
        puls    a
        puls    b,x
        rts

* Decode first pressed key → ASCII (0 if none/unknown)
KeyDecode
        clr     ColN
kdc1    leax    ColTab,pcr
        lda     ColN
        lda     a,x
        sta     PIA0D
        lda     PIA0
        anda    #$7F
        cmpa    #$7F
        bne     kdc_hit
        inc     ColN
        lda     ColN
        cmpa    #7
        blo     kdc1
        clra
        bra     kdc_done
kdc_hit sta     RowBits
        * invert: pressed bits become 1 for finding
        eora    #$7F
        sta     RowBits
        clr     RowN
kdc_r   lsr     RowBits
        bcs     kdc_row         ; found a 1 = pressed
        inc     RowN
        lda     RowN
        cmpa    #7
        blo     kdc_r
        clra
        bra     kdc_done
kdc_row lda     ColN
        ldb     #7
        mul
        addb    RowN
        clra
        tfr     d,x
        leax    KeyMap,x
        lda     ,x
kdc_done
        pshs    a
        lda     #$FF
        sta     PIA0D
        puls    a
        rts

* CoCo keyboard columns (PB0..PB6). Active-low select.
ColTab  fcb     $FE,$FD,$FB,$F7,$EF,$DF,$BF
*
* KeyMap[col*7+row] — standard CoCo layout (approx; enough for game keys)
* col0 @ A B C D E F
KeyMap  fcb     '@,'A,'B,'C,'D,'E,'F
        fcb     'G,'H,'I,'J,'K,'L,'M
        fcb     'N,'O,'P,'Q,'R,'S,'T
        fcb     'U,'V,'W,'X,'Y,'Z,13
        fcb     '0,'1,'2,'3,'4,'5,'6
        fcb     '7,'8,'9,':,';,32,32
        fcb     13,12,8,9,10,0,0

* Sound / RNG
***********************************************************************
SoundInit
        lda     PIA1CRA
        ora     #$08
        sta     PIA1CRA
        lda     #$3C
        sta     PIA1CRB
        sta     PIA2CRB
        rts

Beep
        pshs    a,b,x
        tsta
        beq     b0
        cmpa    #1
        beq     b1
        ldb     #6
        ldx     #10
        bra     bg
b0      ldb     #3
        ldx     #14
        bra     bg
b1      ldb     #5
        ldx     #11
bg      lda     #$30
bi      sta     DAC
        eora    #$3F
        sta     DAC
        pshs    x
bd      leax    -1,x
        bne     bd
        puls    x
        deca
        bne     bi
        decb
        bne     bg
        puls    a,b,x
        rts

SeedRnd
        lda     $0113
        bne     srok
        lda     #$5A
srok    sta     Rnd
        rts
Rand
        lda     Rnd
        lsra
        bcc     rok
        eora    #$B4
rok     sta     Rnd
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

***********************************************************************
* 5x7 font ASCII 32..90 (59 glyphs x 5 cols). Column-major; bit0 = TOP.
* Counts: 16 punct (32-47) + 10 digits + 7 (:..@) + 26 letters = 59
***********************************************************************
Font
        * 32 space .. 47 /
        fcb     0,0,0,0,0
        fcb     0,0,$5F,0,0
        fcb     0,7,0,7,0
        fcb     $14,$7F,$14,$7F,$14
        fcb     $24,$2A,$7F,$2A,$12
        fcb     $23,$13,$08,$64,$62
        fcb     $36,$49,$55,$22,$50
        fcb     0,5,3,0,0
        fcb     0,$1C,$22,$41,0
        fcb     0,$41,$22,$1C,0
        fcb     $14,$08,$3E,$08,$14
        fcb     $08,$08,$3E,$08,$08
        fcb     0,$50,$30,0,0
        fcb     $08,$08,$08,$08,$08
        fcb     0,$60,$60,0,0
        fcb     $20,$10,$08,$04,$02
        * 48-57 digits 0-9
        fcb     $3E,$51,$49,$45,$3E
        fcb     0,$42,$7F,$40,0
        fcb     $42,$61,$51,$49,$46
        fcb     $21,$41,$45,$4B,$31
        fcb     $18,$14,$12,$7F,$10
        fcb     $27,$45,$45,$45,$39
        fcb     $3C,$4A,$49,$49,$30
        fcb     $01,$71,$09,$05,$03
        fcb     $36,$49,$49,$49,$36
        fcb     $06,$49,$49,$29,$1E
        * 58-64 : ; < = > ? @
        fcb     0,$36,$36,0,0
        fcb     0,$56,$36,0,0
        fcb     $08,$14,$22,$41,0
        fcb     $14,$14,$14,$14,$14
        fcb     0,$41,$22,$14,$08
        fcb     $02,$01,$51,$09,$06
        fcb     $32,$49,$79,$41,$3E
        * 65-90 A-Z
        fcb     $7E,$11,$11,$11,$7E
        fcb     $7F,$49,$49,$49,$36
        fcb     $3E,$41,$41,$41,$22
        fcb     $7F,$41,$41,$22,$1C
        fcb     $7F,$49,$49,$49,$41
        fcb     $7F,$09,$09,$09,$01
        fcb     $3E,$41,$49,$49,$7A
        fcb     $7F,$08,$08,$08,$7F
        fcb     0,$41,$7F,$41,0
        fcb     $20,$40,$41,$3F,$01
        fcb     $7F,$08,$14,$22,$41
        fcb     $7F,$40,$40,$40,$40
        fcb     $7F,$02,$0C,$02,$7F
        fcb     $7F,$04,$08,$10,$7F
        fcb     $3E,$41,$41,$41,$3E
        fcb     $7F,$09,$09,$09,$06
        fcb     $3E,$41,$51,$21,$5E
        fcb     $7F,$09,$19,$29,$46
        fcb     $46,$49,$49,$49,$31
        fcb     $01,$01,$7F,$01,$01
        fcb     $3F,$40,$40,$40,$3F
        fcb     $1F,$20,$40,$20,$1F
        fcb     $3F,$40,$38,$40,$3F
        fcb     $63,$14,$08,$14,$63
        fcb     $07,$08,$70,$08,$07
        fcb     $61,$51,$49,$45,$43

***********************************************************************
* Strings
***********************************************************************
TTitle  fcn     "SEA BATTLE ML"
TSub    fcn     "PMODE4 DUAL BOARD"
TCtrl   fcn     "WASD MOVE  R ROTATE"
TCtrl2  fcn     "SPACE FIRE/PLACE  A AUTO"
TGo     fcn     "PRESS ANY KEY"
TPlace  fcn     "PLACE FLEET"
TShip   fcn     "SHIP"
THV     fcn     ""
TH      fcn     "HORIZ"
TV      fcn     "VERT"
THint   fcn     "R ROT  A AUTO  SPACE PUT"
TReady  fcn     "READY - KEY"
TComp   fcn     "COMPUTER PLACES..."
TYou    fcn     "YOUR FLEET"
TRad    fcn     "RADAR"
TStat   fcn     ""
TScE    fcn     "E:"
TScY    fcn     " Y:"
TMHit   fcn     "HIT! KEY"
TMMiss  fcn     "MISS KEY"
TMSunk  fcn     "SUNK! KEY"
TMAlr   fcn     "ALREADY KEY"
TMComp  fcn     "COMPUTER..."
TMComp2 fcn     "COMP DONE KEY"
TWin    fcn     "YOU WIN!"
TLose   fcn     "YOU LOSE"
TmpCh   zmb     1

***********************************************************************
* Variables (in LOADM image)
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
