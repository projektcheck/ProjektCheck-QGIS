<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.10.1-A Coruña" labelsEnabled="1">
  <renderer-v2 forceraster="0" type="singleSymbol" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol type="fill" name="0" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="35,139,69,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="76,76,76,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.2" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="fillColor">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="coalesce(ramp_color(create_ramp(map(0,'#67000d',0.13,'#a50f15',0.26,'#cb181d',0.39,'#ef3b2c',0.52,'#fb6a4a',0.65,'#fc9272',0.78,'#fcbba1',0.9,'#fee0d2',1,'#fff5f0')),scale_linear(IF (&quot;summe_einnahmen&quot; > 0, NULL, &quot;summe_einnahmen&quot;), minimum(&quot;summe_einnahmen&quot;), 0, 0, 1)), '#238b45')" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontItalic="0" fontSize="8" fontWordSpacing="0" blendMode="0" fontStrikeout="0" namedStyle="Standard" previewBkgrdColor="255,255,255,255" fontSizeUnit="Point" fontSizeMapUnitScale="3x:0,0,0,0,0,0" useSubstitutions="0" fieldName=" format_number(round( &quot;summe_einnahmen&quot;),0) || '€'" fontFamily="MS Shell Dlg 2" fontLetterSpacing="0" textColor="0,0,0,255" fontWeight="50" fontCapitals="0" textOpacity="1" fontUnderline="0" textOrientation="horizontal" isExpression="1" fontKerning="1" multilineHeight="1">
        <text-buffer bufferDraw="1" bufferSize="1" bufferBlendMode="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSizeUnits="MM" bufferColor="255,255,255,255" bufferNoFill="1" bufferOpacity="1" bufferJoinStyle="128"/>
        <background shapeRadiiX="0" shapeBorderColor="128,128,128,255" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeOffsetUnit="MM" shapeJoinStyle="64" shapeDraw="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeRotation="0" shapeType="0" shapeOffsetY="0" shapeOffsetX="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM" shapeFillColor="255,255,255,255" shapeSizeX="0" shapeBorderWidth="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiUnit="MM" shapeSizeY="0" shapeRotationType="0" shapeSizeType="0" shapeBlendMode="0" shapeSizeUnit="MM" shapeRadiiY="0">
          <symbol type="marker" name="markerSymbol" force_rhr="0" alpha="1" clip_to_extent="1">
            <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
              <prop v="0" k="angle"/>
              <prop v="243,166,178,255" k="color"/>
              <prop v="1" k="horizontal_anchor_point"/>
              <prop v="bevel" k="joinstyle"/>
              <prop v="circle" k="name"/>
              <prop v="0,0" k="offset"/>
              <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
              <prop v="MM" k="offset_unit"/>
              <prop v="35,35,35,255" k="outline_color"/>
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
                  <Option type="QString" value="" name="name"/>
                  <Option name="properties"/>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadius="0" shadowRadiusAlphaOnly="0" shadowRadiusUnit="MM" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowOffsetUnit="MM" shadowOpacity="0" shadowOffsetGlobal="1" shadowScale="100" shadowBlendMode="6" shadowUnder="0" shadowDraw="0" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" decimals="3" formatNumbers="0" useMaxLineLengthForAutoWrap="1" addDirectionSymbol="0" rightDirectionSymbol=">" reverseDirectionSymbol="0" plussign="0" placeDirectionSymbol="0" autoWrapLength="0" multilineAlign="0" leftDirectionSymbol="&lt;"/>
      <placement placementFlags="10" layerType="PolygonGeometry" repeatDistance="0" geometryGeneratorEnabled="0" centroidInside="0" distMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" preserveRotation="1" priority="5" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleOut="-25" repeatDistanceUnits="MM" yOffset="0" dist="0" distUnits="MM" xOffset="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetType="0" overrunDistance="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" rotationAngle="0" geometryGeneratorType="PointGeometry" placement="1" geometryGenerator="" centroidWhole="0" overrunDistanceUnit="MM" quadOffset="4" maxCurvedCharAngleIn="25" fitInPolygonOnly="0"/>
      <rendering obstacle="1" fontLimitPixelSize="0" scaleMin="0" mergeLines="0" drawLabels="1" limitNumLabels="0" displayAll="0" labelPerPart="0" fontMinPixelSize="3" fontMaxPixelSize="10000" scaleVisibility="0" obstacleFactor="1" zIndex="0" upsidedownLabels="0" minFeatureSize="0" maxNumLabels="2000" obstacleType="0" scaleMax="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option name="properties"/>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" value="pole_of_inaccessibility" name="anchorPoint"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
          <Option type="bool" value="false" name="drawToAllParts"/>
          <Option type="QString" value="0" name="enabled"/>
          <Option type="QString" value="&lt;symbol type=&quot;line&quot; name=&quot;symbol&quot; force_rhr=&quot;0&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; locked=&quot;0&quot; pass=&quot;0&quot; enabled=&quot;1&quot;>&lt;prop v=&quot;square&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;bevel&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;60,60,60,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;0.3&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol"/>
          <Option type="double" value="0" name="minLength"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale"/>
          <Option type="QString" value="MM" name="minLengthUnit"/>
          <Option type="double" value="0" name="offsetFromAnchor"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromAnchorUnit"/>
          <Option type="double" value="0" name="offsetFromLabel"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
