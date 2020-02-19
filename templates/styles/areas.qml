<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" minScale="1e+08" readOnly="1" simplifyMaxScale="1" simplifyLocal="1" version="3.10.1-A Coruña" simplifyDrawingTol="1" maxScale="0" labelsEnabled="0" simplifyDrawingHints="1" styleCategories="AllStyleCategories" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol type="fill" alpha="1" force_rhr="0" clip_to_extent="1" name="0">
        <layer locked="0" enabled="1" pass="0" class="LinePatternFill">
          <prop v="45" k="angle"/>
          <prop v="55,126,184,255" k="color"/>
          <prop v="2" k="distance"/>
          <prop v="3x:0,0,0,0,0,0" k="distance_map_unit_scale"/>
          <prop v="MM" k="distance_unit"/>
          <prop v="0.26" k="line_width"/>
          <prop v="3x:0,0,0,0,0,0" k="line_width_map_unit_scale"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol type="line" alpha="1" force_rhr="0" clip_to_extent="1" name="@0@0">
            <layer locked="0" enabled="1" pass="0" class="SimpleLine">
              <prop v="square" k="capstyle"/>
              <prop v="5;2" k="customdash"/>
              <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
              <prop v="MM" k="customdash_unit"/>
              <prop v="0" k="draw_inside_polygon"/>
              <prop v="bevel" k="joinstyle"/>
              <prop v="128,128,128,255" k="line_color"/>
              <prop v="solid" k="line_style"/>
              <prop v="0.3" k="line_width"/>
              <prop v="MM" k="line_width_unit"/>
              <prop v="0" k="offset"/>
              <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
              <prop v="MM" k="offset_unit"/>
              <prop v="0" k="ring_filter"/>
              <prop v="0" k="use_custom_dash"/>
              <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option name="properties"/>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer locked="0" enabled="1" pass="0" class="SimpleFill">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="119,119,119,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="101,101,101,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.46" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="no" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory width="15" scaleBasedVisibility="0" backgroundAlpha="255" penAlpha="255" labelPlacementMethod="XHeight" scaleDependency="Area" penColor="#000000" maxScaleDenominator="1e+08" enabled="0" sizeType="MM" rotationOffset="270" lineSizeScale="3x:0,0,0,0,0,0" lineSizeType="MM" penWidth="0" height="15" opacity="1" backgroundColor="#ffffff" minimumSize="0" minScaleDenominator="0" diagramOrientation="Up" sizeScale="3x:0,0,0,0,0,0" barWidth="5">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" showAll="1" placement="1" dist="0" obstacle="0" priority="0" zIndex="0">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option type="Map" name="QgsGeometryGapCheck">
        <Option type="double" value="0" name="allowedGapsBuffer"/>
        <Option type="bool" value="false" name="allowedGapsEnabled"/>
        <Option type="QString" value="" name="allowedGapsLayer"/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <fieldConfiguration>
    <field name="fid">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nutzungsart">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="name">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="aufsiedlungsdauer">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="validiert">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="beginn_nutzung">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ags_bkg">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="gemeinde_typ">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="gemeinde_name">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="we_gesamt">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ap_gesamt">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ap_ist_geschaetzt">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="vf_gesamt">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ew">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="wege_gesamt">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="wege_miv">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="fid" name="" index="0"/>
    <alias field="nutzungsart" name="" index="1"/>
    <alias field="name" name="" index="2"/>
    <alias field="aufsiedlungsdauer" name="" index="3"/>
    <alias field="validiert" name="" index="4"/>
    <alias field="beginn_nutzung" name="" index="5"/>
    <alias field="ags_bkg" name="" index="6"/>
    <alias field="gemeinde_typ" name="" index="7"/>
    <alias field="gemeinde_name" name="" index="8"/>
    <alias field="we_gesamt" name="" index="9"/>
    <alias field="ap_gesamt" name="" index="10"/>
    <alias field="ap_ist_geschaetzt" name="" index="11"/>
    <alias field="vf_gesamt" name="" index="12"/>
    <alias field="ew" name="" index="13"/>
    <alias field="wege_gesamt" name="" index="14"/>
    <alias field="wege_miv" name="" index="15"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="fid" expression="" applyOnUpdate="0"/>
    <default field="nutzungsart" expression="" applyOnUpdate="0"/>
    <default field="name" expression="" applyOnUpdate="0"/>
    <default field="aufsiedlungsdauer" expression="" applyOnUpdate="0"/>
    <default field="validiert" expression="" applyOnUpdate="0"/>
    <default field="beginn_nutzung" expression="" applyOnUpdate="0"/>
    <default field="ags_bkg" expression="" applyOnUpdate="0"/>
    <default field="gemeinde_typ" expression="" applyOnUpdate="0"/>
    <default field="gemeinde_name" expression="" applyOnUpdate="0"/>
    <default field="we_gesamt" expression="" applyOnUpdate="0"/>
    <default field="ap_gesamt" expression="" applyOnUpdate="0"/>
    <default field="ap_ist_geschaetzt" expression="" applyOnUpdate="0"/>
    <default field="vf_gesamt" expression="" applyOnUpdate="0"/>
    <default field="ew" expression="" applyOnUpdate="0"/>
    <default field="wege_gesamt" expression="" applyOnUpdate="0"/>
    <default field="wege_miv" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint field="fid" unique_strength="1" exp_strength="0" constraints="3" notnull_strength="1"/>
    <constraint field="nutzungsart" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="name" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="aufsiedlungsdauer" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="validiert" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="beginn_nutzung" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="ags_bkg" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="gemeinde_typ" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="gemeinde_name" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="we_gesamt" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="ap_gesamt" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="ap_ist_geschaetzt" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="vf_gesamt" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="ew" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="wege_gesamt" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint field="wege_miv" unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="fid" exp="" desc=""/>
    <constraint field="nutzungsart" exp="" desc=""/>
    <constraint field="name" exp="" desc=""/>
    <constraint field="aufsiedlungsdauer" exp="" desc=""/>
    <constraint field="validiert" exp="" desc=""/>
    <constraint field="beginn_nutzung" exp="" desc=""/>
    <constraint field="ags_bkg" exp="" desc=""/>
    <constraint field="gemeinde_typ" exp="" desc=""/>
    <constraint field="gemeinde_name" exp="" desc=""/>
    <constraint field="we_gesamt" exp="" desc=""/>
    <constraint field="ap_gesamt" exp="" desc=""/>
    <constraint field="ap_ist_geschaetzt" exp="" desc=""/>
    <constraint field="vf_gesamt" exp="" desc=""/>
    <constraint field="ew" exp="" desc=""/>
    <constraint field="wege_gesamt" exp="" desc=""/>
    <constraint field="wege_miv" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column type="field" width="-1" name="fid" hidden="0"/>
      <column type="field" width="-1" name="nutzungsart" hidden="0"/>
      <column type="field" width="-1" name="name" hidden="0"/>
      <column type="field" width="-1" name="aufsiedlungsdauer" hidden="0"/>
      <column type="field" width="-1" name="validiert" hidden="0"/>
      <column type="field" width="-1" name="beginn_nutzung" hidden="0"/>
      <column type="field" width="-1" name="ags_bkg" hidden="0"/>
      <column type="field" width="-1" name="gemeinde_name" hidden="0"/>
      <column type="field" width="-1" name="we_gesamt" hidden="0"/>
      <column type="field" width="-1" name="ap_gesamt" hidden="0"/>
      <column type="field" width="-1" name="vf_gesamt" hidden="0"/>
      <column type="field" width="-1" name="ew" hidden="0"/>
      <column type="field" width="-1" name="wege_gesamt" hidden="0"/>
      <column type="field" width="-1" name="wege_miv" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
      <column type="field" width="-1" name="gemeinde_typ" hidden="0"/>
      <column type="field" width="-1" name="ap_ist_geschaetzt" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="ags_bkg"/>
    <field editable="1" name="anteil_bau"/>
    <field editable="1" name="anteil_finanzen"/>
    <field editable="1" name="anteil_grosshandel"/>
    <field editable="1" name="anteil_oeffentlich"/>
    <field editable="1" name="anteil_sonstige"/>
    <field editable="1" name="anteil_verarbeitend"/>
    <field editable="1" name="ap_gesamt"/>
    <field editable="1" name="ap_ist_geschaetzt"/>
    <field editable="1" name="aperiodischer_bedarf"/>
    <field editable="1" name="aufsiedlungsdauer"/>
    <field editable="1" name="baumarkt"/>
    <field editable="1" name="beginn_nutzung"/>
    <field editable="1" name="ew"/>
    <field editable="1" name="ew_je_we_efh"/>
    <field editable="1" name="ew_je_we_mfh"/>
    <field editable="1" name="ew_je_we_rh"/>
    <field editable="1" name="ew_je_we_zfh"/>
    <field editable="1" name="fid"/>
    <field editable="1" name="gemeinde_name"/>
    <field editable="1" name="gemeinde_typ"/>
    <field editable="1" name="lebensmittel"/>
    <field editable="1" name="moebel"/>
    <field editable="1" name="name"/>
    <field editable="1" name="nutzungsart"/>
    <field editable="1" name="periodischer_bedarf"/>
    <field editable="1" name="validiert"/>
    <field editable="1" name="vf_gesamt"/>
    <field editable="1" name="we_efh"/>
    <field editable="1" name="we_gesamt"/>
    <field editable="1" name="we_mfh"/>
    <field editable="1" name="we_rh"/>
    <field editable="1" name="we_zfh"/>
    <field editable="1" name="wege_gesamt"/>
    <field editable="1" name="wege_miv"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="ags_bkg"/>
    <field labelOnTop="0" name="anteil_bau"/>
    <field labelOnTop="0" name="anteil_finanzen"/>
    <field labelOnTop="0" name="anteil_grosshandel"/>
    <field labelOnTop="0" name="anteil_oeffentlich"/>
    <field labelOnTop="0" name="anteil_sonstige"/>
    <field labelOnTop="0" name="anteil_verarbeitend"/>
    <field labelOnTop="0" name="ap_gesamt"/>
    <field labelOnTop="0" name="ap_ist_geschaetzt"/>
    <field labelOnTop="0" name="aperiodischer_bedarf"/>
    <field labelOnTop="0" name="aufsiedlungsdauer"/>
    <field labelOnTop="0" name="baumarkt"/>
    <field labelOnTop="0" name="beginn_nutzung"/>
    <field labelOnTop="0" name="ew"/>
    <field labelOnTop="0" name="ew_je_we_efh"/>
    <field labelOnTop="0" name="ew_je_we_mfh"/>
    <field labelOnTop="0" name="ew_je_we_rh"/>
    <field labelOnTop="0" name="ew_je_we_zfh"/>
    <field labelOnTop="0" name="fid"/>
    <field labelOnTop="0" name="gemeinde_name"/>
    <field labelOnTop="0" name="gemeinde_typ"/>
    <field labelOnTop="0" name="lebensmittel"/>
    <field labelOnTop="0" name="moebel"/>
    <field labelOnTop="0" name="name"/>
    <field labelOnTop="0" name="nutzungsart"/>
    <field labelOnTop="0" name="periodischer_bedarf"/>
    <field labelOnTop="0" name="validiert"/>
    <field labelOnTop="0" name="vf_gesamt"/>
    <field labelOnTop="0" name="we_efh"/>
    <field labelOnTop="0" name="we_gesamt"/>
    <field labelOnTop="0" name="we_mfh"/>
    <field labelOnTop="0" name="we_rh"/>
    <field labelOnTop="0" name="we_zfh"/>
    <field labelOnTop="0" name="wege_gesamt"/>
    <field labelOnTop="0" name="wege_miv"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>fid</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
