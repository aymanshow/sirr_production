<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fo="http://www.w3.org/1999/XSL/Format">

    <xsl:template match="/">
        <xsl:call-template name="rml" />
    </xsl:template>

    <xsl:template name="rml">
		<document filename="example.pdf">
			<template pageSize="29.7cm,21cm" leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm"
				title="Journals" author="Generated by Moldeo Int, Cristian S. Rocha" allowSplitting="20">
				<pageTemplate id="first">
					<pageGraphics>
                        <setFont name="Helvetica-Bold" size="16"/>
                        <drawCentredString x="15.7cm" y="20.0cm">Reporte Detallado</drawCentredString>
                        <setFont name="Helvetica" size="8"/>
                        <drawRightString x="28.0cm" y="20.0cm"><xsl:value-of select="/report/date"/></drawRightString>
					</pageGraphics>
					<frame id="col1" x1="1.0cm" y1="1.0cm" width="27.0cm" height="19cm"/>
				</pageTemplate>
			</template>

			<stylesheet>
				<paraStyle name="small" fontName="Helvetica" fontSize="5" leading="7"/>
				<paraStyle name="normal" fontName="Helvetica" fontSize="8" leading="10"/>
				<paraStyle name="big" fontName="Helvetica" fontSize="10" leading="12"/>
				<blockTableStyle id="head-table">
					<blockFont name="Helvetica" size="12" start="0,0" stop="-1,-1"/>
					<blockBackground colorName="black" start="0,0" stop="-1,-1"/>
					<blockTextColor colorName="white" start="0,0" stop="-1,-1"/>
                    <blockTopPadding length="15" start="0,0" stop="-1,-1"/>
                    <blockBottomPadding length="10" start="0,0" stop="-1,-1"/>
                </blockTableStyle>
				<blockTableStyle id="journal-table">
					<lineStyle kind="GRID" colorName="#e6e6e6"/>
					<blockBackground colorName="lightgrey" start="0,0" stop="-1,1"/>
					<!--blockBackground colorName="lightgrey" start="0,-1" stop="-1,-1"/-->
					<blockValign value="MIDDLE" start="0,0" stop="-1,1"/>
					<blockAlignment value="CENTER" start="0,0" stop="-1,1"/>
					<blockValign value="TOP" start="0,2" stop="-1,-1"/>
					<blockFont name="Helvetica" size="5" start="0,1" stop="-1,1"/>
					<blockFont name="Helvetica" size="5" start="2,2" stop="-1,-1"/>
					<!--blockSpan start="0,0" stop="0,1"/>
					<blockSpan start="1,0" stop="1,1"/>
					<blockSpan start="2,0" stop="-4,0"/>
					<blockSpan start="-3,0" stop="-1,0"/-->
					<!--blockSpan start="-2,0" stop="-2,1"/-->
					<!--blockSpan start="-1,0" stop="-1,1"/-->
				</blockTableStyle>
			</stylesheet>

			<story>
                <xsl:apply-templates select="report/entry"/>
			</story>
		</document>
    </xsl:template>

    <xsl:template match="entry">
        <para>.</para>
        <blockTable colWidths="100.0,200.0,50.0,100.0,320.0" style="head-table">
        <tr>
            <td>Nombre</td><td><xsl:value-of select='employee/name'/></td>
            <td>Legajo</td><td><xsl:value-of select='employee/otherid'/></td>
            <td></td>
        </tr>
        </blockTable>

        <xsl:apply-templates select="journals"/>

        <!--nextFrame/-->
    </xsl:template>

    <xsl:template match="journals">
        <blockTable
		colWidths="70,100,30,30,30,30,30,30,30,30,30,30,30,90,90,90"
                repeatRows="2"
		style="journal-table">
            <tr>
                <td><para>Fecha</para><para>Turno. Sector</para></td>
                <td>Asistencia</td>
                <td>Horas</td> <!-- Normales -->
                <td>-</td> <!-- Extra 100% -->
                <td>-</td> <!-- Extra 50% -->
                <td>-</td> <!-- Nocturnas -->
                <td>-</td> <!-- Enfermedad -->
                <td>-</td> <!-- ART -->
                <td>-</td> <!-- Vacaciones -->
                <td>-</td> <!-- Sindicato -->
                <td>-</td> <!-- Feriado -->
                <td>-</td> <!-- Licencias -->
                <td>-</td> <!-- Faltas -->
                <td>Detalles</td> <!-- Licencias -->
                <td>-</td> <!-- Faltas -->
                <td>-</td> <!-- Anotaciones -->
            </tr>
            <tr>
                <td>-</td>
                <td>-</td>
		<!-- Horas -->
                <td>Normales</td>
                <td>Extra 100%</td>
                <td>Extra 50%</td>
                <td>Nocturnas</td>
                <td>Enfermedad</td>
                <td>ART</td>
                <td>Vacaciones</td>
                <td>Sindicato</td>
                <td>Feriado</td>
                <td>Licencias</td>
                <td>Faltas</td>
		<!-- Detalles -->
                <td>Licencias</td>
                <td>Faltas</td>
                <td>Anotaciones</td>
            </tr>
            <xsl:for-each select="journal">
            <tr>
                <td>
                    <para style='big'><xsl:value-of select='date'/></para>
                    <para style='small'><xsl:value-of select='turn_id'/>. <xsl:value-of select='department_id'/></para>
                </td>
                <td>
                    <xsl:for-each select='attendances/attendance'>
                        <para style='small'>
                            <xsl:value-of select='time'/> . <b>
                                <xsl:if test="action = 'sign_in'">&#8594;]</xsl:if>
                                <xsl:if test="action = 'sign_out'">&#8592;]</xsl:if>
                            </b> . <xsl:value-of select='reason'/>
                        </para>
                    </xsl:for-each>
                </td>
                <td><xsl:value-of select='v_normal_hours'/></td>
                <td><xsl:value-of select='v_full_extra_hours'/></td>
                <td><xsl:value-of select='v_half_extra_hours'/></td>
                <td><xsl:value-of select='v_night_hours'/></td>
                <td><xsl:value-of select='v_sick_hours'/></td>
                <td><xsl:value-of select='v_art_hours'/></td>
                <td><xsl:value-of select='v_vacation_hours'/></td>
                <td><xsl:value-of select='v_sindicate_hours'/></td>
                <td><xsl:value-of select='v_national_hours'/></td>
                <td><xsl:value-of select='v_licenses_hours'/></td>
                <td><xsl:value-of select='v_fault_hours'/></td>
                <td>
                    <xsl:for-each select='holidays/legals/holiday'>
                        <para style='small'><xsl:value-of select='date-from'/> - <xsl:value-of select='date-to'/> : <xsl:value-of select='status'/>;
				<xsl:value-of select='name'/></para>
                    </xsl:for-each>
                </td>
                <td>
                    <xsl:for-each select='holidays/out/holiday'>
                        <para style='small'><xsl:value-of select='date-from'/> - <xsl:value-of select='date-to'/> : <xsl:value-of select='status'/>;
				<xsl:value-of select='name'/></para>
                    </xsl:for-each>
                </td>
                <td><para style='small'><xsl:value-of select='note'/></para></td>
            </tr>
            </xsl:for-each>
            <tr>
                <td>Total</td>
                <td></td>
                <td><xsl:value-of select='sums/v_normal_hours'/></td>
                <td><xsl:value-of select='sums/v_extra_hours'/></td>
                <td><xsl:value-of select='sums/v_half_extra_hours'/></td>
                <td><xsl:value-of select='sums/v_night_hours'/></td>
                <td><xsl:value-of select='sums/v_sick_hours'/></td>
                <td><xsl:value-of select='sums/v_art_hours'/></td>
                <td><xsl:value-of select='sums/v_holiday_hours'/></td>
                <td></td>
                <td></td>
            </tr>
        </blockTable>

    </xsl:template>


</xsl:stylesheet>

<!--
     vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
     -->
