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

* Board geometry (pixels)
CELL    equ     10
* Left fleet board top-left of cell (0,0)
LX0     equ     16
LY0     equ     28
* Right radar board
RX0     equ     144
RY0     equ     28

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
        lda     #5
        sta     SL
        sta     SR
        lda     #4
        sta     SL+1
        sta     SR+1
        lda     #3
        sta     SL+2
        sta     SR+2
        sta     SL+3
        sta     SR+3
        lda     #2
        sta     SL+4
        sta     SR+4
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
        lbsr    DrawBattle      ; left=PS right=RD (empty)
        lbsr    DrawPlaceHUD
        lbsr    DrawCursorLeft
pp_in
        lbsr    WaitKey
        cmpa    #'A
        lbeq    pp_auto
        cmpa    #'a
        lbeq    pp_auto
        cmpa    #'R
        lbeq    pp_rot
        cmpa    #'r
        lbeq    pp_rot
        cmpa    #9              ; right arrow (some ROMs) — also D
        lbeq    pp_r
        cmpa    #'D
        lbeq    pp_r
        cmpa    #'d
        lbeq    pp_r
        cmpa    #8              ; left / BS / A
        lbeq    pp_l
        cmpa    #'A
        beq     pp_lskip        ; A is auto — already handled
pp_lskip
        cmpa    #'S
        lbeq    pp_d
        cmpa    #'s
        lbeq    pp_d
        cmpa    #10             ; down
        lbeq    pp_d
        cmpa    #'W
        lbeq    pp_u
        cmpa    #'w
        lbeq    pp_u
        cmpa    #94             ; up arrow often
        lbeq    pp_u
        cmpa    #32             ; space
        lbeq    pp_put
        cmpa    #13             ; enter
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
        inc     CurC
        lbra    pp_draw
pp_l    lda     CurC
        cmpa    #1
        lbls    pp_in
        dec     CurC
        lbra    pp_draw
pp_d    lda     CurR
        cmpa    #10
        lbhs    pp_in
        inc     CurR
        lbra    pp_draw
pp_u    lda     CurR
        cmpa    #1
        lbls    pp_in
        dec     CurR
        lbra    pp_draw
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
        lbra    pp_draw
pp_auto
        lda     #0
        lbsr    AutoPlaceFleet
        ; mark all ships placed
        lda     #6
        sta     ShipId
        lda     #1
        lbsr    Beep
pp_done
        lbsr    DrawBattle
        leax    TReady,pcr
        lda     #50
        ldb     #180
        lbsr    DrawStr
        lbsr    WaitKey
        rts

DrawPlaceHUD
        leax    TPlace,pcr
        lda     #8
        ldb     #4
        lbsr    DrawStr
        leax    TShip,pcr
        lda     #8
        ldb     #14
        lbsr    DrawStr
        lda     ShipId
        adda    #'0
        sta     TmpCh
        leax    TmpCh,pcr
        lda     #80
        ldb     #14
        lbsr    DrawStr
        leax    THV,pcr
        lda     #100
        ldb     #14
        lbsr    DrawStr
        lda     Horiz
        beq     dph_v
        leax    TH,pcr
        bra     dph_w
dph_v   leax    TV,pcr
dph_w   lda     #160
        ldb     #14
        lbsr    DrawStr
        leax    THint,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        rts

PlaceEnemyFleet
        leax    TComp,pcr
        lda     #40
        ldb     #90
        lbsr    GfxCls
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
pt_d    lbsr    DrawBattle
        lbsr    DrawBattleHUD
        lbsr    DrawCursorRight
pt_i    lbsr    WaitKey
        cmpa    #'F
        lbeq    pt_d
        cmpa    #'f
        lbeq    pt_d
        cmpa    #'D
        lbeq    pt_r
        cmpa    #'d
        lbeq    pt_r
        cmpa    #9
        lbeq    pt_r
        cmpa    #'A
        lbeq    pt_l
        cmpa    #'a
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
        inc     CurC
        lbra    pt_d
pt_l    lda     CurC
        cmpa    #1
        lbls    pt_i
        dec     CurC
        lbra    pt_d
pt_dn   lda     CurR
        cmpa    #10
        lbhs    pt_i
        inc     CurR
        lbra    pt_d
pt_up   lda     CurR
        cmpa    #1
        lbls    pt_i
        dec     CurR
        lbra    pt_d
pt_fire
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        lda     #1
        lbsr    ApplyShot
        lbsr    DrawBattle
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
        lbra    pt_d
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
        lbsr    DrawBattle
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
* Draw PMODE 4 dual boards
***********************************************************************
DrawBattle
        lbsr    GfxCls
        * left PS
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lbsr    DrawOneBoard
        * right RD
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lbsr    DrawOneBoard
        * scores
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

* BoardWhich 0=PS fleet glyphs 1=RD radar glyphs
DrawOneBoard
        * frame
        lda     BX0
        deca
        ldb     BY0
        decb
        sta     RX
        stb     RY
        lda     #CELL*10+2
        sta     Wd
        sta     Ht
        lbsr    DrawRect
        lda     #1
        sta     RR
dobr    lda     #1
        sta     CC
dobc    lbsr    CellGlyph
        sta     GType
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
        lbsr    DrawCell
        inc     CC
        lda     CC
        cmpa    #11
        blo     dobc
        inc     RR
        lda     RR
        cmpa    #11
        blo     dobr
        rts

CellGlyph
        lda     BoardWhich
        bne     cg_r
        ldx     #PS
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        tsta
        beq     cg0
        cmpa    #6
        beq     cg2
        cmpa    #7
        beq     cg3
        lda     #1              ; ship
        rts
cg_r    ldx     #RD
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        tsta
        beq     cg0
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

* GType: 0 empty 1 ship 2 miss 3 hit — draw CELL x CELL at X0,Y0
DrawCell
        lda     GType
        beq     dc_empty
        cmpa    #1
        beq     dc_ship
        cmpa    #2
        beq     dc_miss
        * hit = filled + cross later
        lda     X0
        ldb     Y0
        sta     RX
        stb     RY
        lda     #CELL-1
        sta     Wd
        sta     Ht
        lbsr    FillRect2
        rts
dc_ship
        lda     X0
        ldb     Y0
        sta     RX
        stb     RY
        lda     #CELL-1
        sta     Wd
        sta     Ht
        lbsr    FillRect2
        rts
dc_miss
        * hollow circle-ish: small fill center
        lda     X0
        adda    #3
        ldb     Y0
        addb    #3
        sta     RX
        stb     RY
        lda     #3
        sta     Wd
        sta     Ht
        lbsr    FillRect2
        rts
dc_empty
        lda     X0
        adda    #4
        ldb     Y0
        addb    #4
        lbsr    Plot2
        rts

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
        lda     CurC
        deca
        ldb     #CELL
        mul
        addb    BX0
        stb     X0
        lda     CurR
        deca
        ldb     #CELL
        mul
        addb    BY0
        stb     Y0
        lda     X0
        ldb     Y0
        sta     RX
        stb     RY
        lda     #CELL-1
        sta     Wd
        sta     Ht
        lbsr    DrawRect
        rts

***********************************************************************
***********************************************************************
* Low-level PMODE 4 graphics (1 bpp @ GFX)
***********************************************************************
GfxCls
        ldx     #GFX
        ldy     #6144
        clra
gc1     sta     ,x+
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

* 5x7 font, column-major, bit7=top. Index = ASCII-32, glyphs 32..90 only.
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
        lda     #7              ; 7 rows used (bit7..bit1)
        sta     TmpI
        lda     CY
        sta     PY
dc_row  lda     TmpB
        bita    #$80
        beq     dc_s
        lda     CX
        ldb     PY
        lbsr    Plot2
dc_s    lsl     TmpB
        inc     PY
        dec     TmpI
        bne     dc_row
        inc     CX
        dec     TmpL
        bne     dc_col
dcz     rts

***********************************************************************
* Matrix keyboard (no POLCAT). Timeout → Space so game never freezes.
***********************************************************************
WaitKey
        lbsr    KeyWaitPress
        cmpa    #$7F
        beq     wk_to
        lbsr    KeyDecode
        pshs    a
        lbsr    KeyWaitRelease
        puls    a
        rts
wk_to   lda     #32
        rts

KeyRaw
        lda     #$00
        sta     PIA0D
        lda     PIA0
        anda    #$7F
        rts

KeyWaitPress
        ldb     #$50
        ldx     #0
kwp1    lbsr    KeyRaw
        cmpa    #$7F
        bne     kwp2
        leax    -1,x
        bne     kwp1
        decb
        bne     kwp1
        lda     #$7F
        rts
kwp2    rts

KeyWaitRelease
        ldb     #$30
        ldx     #0
kwr1    lbsr    KeyRaw
        cmpa    #$7F
        beq     kwr2
        leax    -1,x
        bne     kwr1
        decb
        bne     kwr1
kwr2    rts

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
        cmpa    #8
        blo     kdc1
        lda     #32
        rts
kdc_hit sta     RowBits
        clr     RowN
kdc_r   lda     RowBits
        rora
        sta     RowBits
        bcc     kdc_row
        inc     RowN
        lda     RowN
        cmpa    #7
        blo     kdc_r
        lda     #32
        rts
kdc_row lda     ColN
        ldb     #7
        mul
        addb    RowN
        clra
        tfr     d,x
        leax    KeyMap,x
        lda     ,x
        rts

ColTab  fcb     $FE,$FD,$FB,$F7,$EF,$DF,$BF,$7F
KeyMap
        fcb     '@,'A,'B,'C,'D,'E,'F
        fcb     'G,'H,'I,'J,'K,'L,'M
        fcb     'N,'O,'P,'Q,'R,'S,'T
        fcb     'U,'V,'W,'X,'Y,'Z,13
        fcb     '0,'1,'2,'3,'4,'5,'6
        fcb     '7,'8,'9,32,32,32,32
        fcb     13,32,8,9,10,32,32
        fcb     32,32,32,32,32,32,32

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
* 5x7 font ASCII 32..90 inclusive (59 glyphs x 5 cols). bit7 = top.
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
