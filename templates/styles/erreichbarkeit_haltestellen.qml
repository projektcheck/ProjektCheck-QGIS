<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" simplifyDrawingHints="1" simplifyDrawingTol="1" minScale="0" simplifyLocal="1" readOnly="0" version="3.6.1-Noosa" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" labelsEnabled="1" simplifyMaxScale="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 enableorderby="0" forceraster="0" type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol alpha="1" clip_to_extent="1" name="0" type="marker" force_rhr="0">
        <layer enabled="1" pass="0" class="SimpleMarker" locked="0">
          <prop v="0" k="angle"/>
          <prop v="153,153,0,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="77,77,77,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="size" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="2*(sqrt(&quot;abfahrten&quot;/pi()))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style textOpacity="1" namedStyle="Standard" textColor="77,77,0,255" fontSize="10" fontCapitals="0" fontUnderline="0" fontFamily="MS Shell Dlg 2" fontWeight="50" fontSizeUnit="Point" fontItalic="0" blendMode="0" fieldName="IF (&quot;abfahrten&quot; > 0, &quot;name&quot; || ' (' || &quot;abfahrten&quot; || ' Abfahrten pro Tag', NULL)" useSubstitutions="0" multilineHeight="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontStrikeout="0" fontWordSpacing="0" fontLetterSpacing="0" previewBkgrdColor="#ffffff" isExpression="1">
        <text-buffer bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferJoinStyle="128" bufferColor="255,255,255,255" bufferBlendMode="0" bufferDraw="1" bufferSize="0,9" bufferNoFill="1" bufferOpacity="1"/>
        <background shapeOffsetY="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSizeType="0" shapeSizeY="0" shapeJoinStyle="64" shapeType="0" shapeDraw="0" shapeRotationType="0" shapeSVGFile="" shapeRadiiX="0" shapeBorderWidthUnit="MM" shapeFillColor="255,255,255,255" shapeOpacity="1" shapeSizeX="0" shapeBorderWidth="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeBlendMode="0" shapeOffsetX="0" shapeRadiiUnit="MM" shapeRadiiY="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBorderColor="128,128,128,255" shapeSizeUnit="MM" shapeOffsetUnit="MM"/>
        <shadow shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadius="1,5" shadowBlendMode="6" shadowOffsetGlobal="1" shadowRadiusAlphaOnly="0" shadowScale="100" shadowOffsetDist="1" shadowOffsetUnit="MM" shadowColor="0,0,0,255" shadowUnder="0" shadowOpacity="0,7" shadowOffsetAngle="135" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowDraw="0" shadowRadiusUnit="MM"/>
        <substitutions/>
      </text-style>
      <text-format placeDirectionSymbol="0" reverseDirectionSymbol="0" formatNumbers="0" plussign="0" addDirectionSymbol="0" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" wrapChar="" multilineAlign="3" leftDirectionSymbol="&lt;" autoWrapLength="0" decimals="3"/>
      <placement maxCurvedCharAngleOut="-25" distUnits="MM" xOffset="0" placement="6" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" fitInPolygonOnly="0" placementFlags="10" quadOffset="4" centroidInside="0" centroidWhole="0" maxCurvedCharAngleIn="25" priority="5" preserveRotation="1" repeatDistanceUnits="MM" dist="0" offsetType="1" distMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" yOffset="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" repeatDistance="0" rotationAngle="0"/>
      <rendering fontMinPixelSize="3" zIndex="0" scaleVisibility="0" fontLimitPixelSize="0" limitNumLabels="0" drawLabels="1" obstacleType="0" scaleMin="0" maxNumLabels="2000" fontMaxPixelSize="10000" labelPerPart="0" upsidedownLabels="0" mergeLines="0" minFeatureSize="0" obstacleFactor="1" scaleMax="0" obstacle="1" displayAll="0"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties"/>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <customproperties>
    <property key="dualview/previewExpressions">
      <value>"fid"</value>
    </property>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="fid">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="abfahrten">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="id_bahn">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="flaechenzugehoerig">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="name">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="fid" index="0" name=""/>
    <alias field="abfahrten" index="1" name=""/>
    <alias field="id_bahn" index="2" name=""/>
    <alias field="flaechenzugehoerig" index="3" name=""/>
    <alias field="name" index="4" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="fid"/>
    <default expression="" applyOnUpdate="0" field="abfahrten"/>
    <default expression="" applyOnUpdate="0" field="id_bahn"/>
    <default expression="" applyOnUpdate="0" field="flaechenzugehoerig"/>
    <default expression="" applyOnUpdate="0" field="name"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" constraints="3" field="fid" unique_strength="1" notnull_strength="1"/>
    <constraint exp_strength="0" constraints="0" field="abfahrten" unique_strength="0" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" field="id_bahn" unique_strength="0" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" field="flaechenzugehoerig" unique_strength="0" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" field="name" unique_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="fid"/>
    <constraint desc="" exp="" field="abfahrten"/>
    <constraint desc="" exp="" field="id_bahn"/>
    <constraint desc="" exp="" field="flaechenzugehoerig"/>
    <constraint desc="" exp="" field="name"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" name="fid" width="-1" type="field"/>
      <column hidden="0" name="abfahrten" width="-1" type="field"/>
      <column hidden="0" name="id_bahn" width="-1" type="field"/>
      <column hidden="0" name="flaechenzugehoerig" width="-1" type="field"/>
      <column hidden="0" name="name" width="-1" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable/>
  <labelOnTop/>
  <widgets/>
  <previewExpression>"fid"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
