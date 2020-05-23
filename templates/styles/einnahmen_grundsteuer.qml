<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.10.1-A Coruña" labelsEnabled="1">
  <renderer-v2 forceraster="0" symbollevels="0" enableorderby="0" type="singleSymbol">
    <symbols>
      <symbol clip_to_extent="1" force_rhr="0" name="0" type="fill" alpha="1">
        <layer enabled="1" class="SimpleFill" pass="0" locked="0">
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
              <Option value="" name="name" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option value="true" name="active" type="bool"/>
                  <Option value="coalesce(ramp_color(create_ramp(map(0,'#67000d',0.13,'#a50f15',0.26,'#cb181d',0.39,'#ef3b2c',0.52,'#fb6a4a',0.65,'#fc9272',0.78,'#fcbba1',0.9,'#fee0d2',1,'#fff5f0')),scale_linear(IF (&quot;grundsteuer&quot; >= 1, NULL, &quot;grundsteuer&quot;), minimum(&quot;grundsteuer&quot;), 1, 1, 1)), '#238b45')" name="expression" type="QString"/>
                  <Option value="3" name="type" type="int"/>
                </Option>
              </Option>
              <Option value="collection" name="type" type="QString"/>
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
      <text-style multilineHeight="1" useSubstitutions="0" fontSizeUnit="Point" isExpression="1" fontLetterSpacing="0" fontWordSpacing="0" fontFamily="MS Shell Dlg 2" blendMode="0" fontCapitals="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" textOrientation="horizontal" namedStyle="Standard" textOpacity="1" fontKerning="1" fontSize="8" fontItalic="0" fieldName=" format_number(round( &quot;grundsteuer&quot;),0) || '€'" fontStrikeout="0" previewBkgrdColor="255,255,255,255" fontUnderline="0" fontWeight="50" textColor="0,0,0,255">
        <text-buffer bufferBlendMode="0" bufferSize="1" bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="1" bufferNoFill="1" bufferOpacity="1" bufferColor="255,255,255,255" bufferJoinStyle="128"/>
        <background shapeSizeType="0" shapeBorderColor="128,128,128,255" shapeSizeUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeDraw="0" shapeSVGFile="" shapeRadiiX="0" shapeOpacity="1" shapeBlendMode="0" shapeRotation="0" shapeOffsetX="0" shapeSizeX="0" shapeRotationType="0" shapeOffsetY="0" shapeJoinStyle="64" shapeRadiiUnit="MM" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeSizeY="0" shapeBorderWidth="0" shapeBorderWidthUnit="MM" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeType="0" shapeOffsetUnit="MM">
          <symbol clip_to_extent="1" force_rhr="0" name="markerSymbol" type="marker" alpha="1">
            <layer enabled="1" class="SimpleMarker" pass="0" locked="0">
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
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowOffsetUnit="MM" shadowRadius="0" shadowColor="0,0,0,255" shadowOpacity="0" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowScale="100" shadowOffsetGlobal="1" shadowRadiusAlphaOnly="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowRadiusUnit="MM" shadowDraw="0" shadowBlendMode="6"/>
        <dd_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" addDirectionSymbol="0" formatNumbers="0" reverseDirectionSymbol="0" plussign="0" autoWrapLength="0" useMaxLineLengthForAutoWrap="1" leftDirectionSymbol="&lt;" decimals="3" rightDirectionSymbol=">" placeDirectionSymbol="0" multilineAlign="0"/>
      <placement xOffset="0" centroidWhole="0" yOffset="0" repeatDistanceUnits="MM" preserveRotation="1" geometryGeneratorEnabled="0" distMapUnitScale="3x:0,0,0,0,0,0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetType="0" distUnits="MM" quadOffset="4" offsetUnits="MM" rotationAngle="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" geometryGenerator="" maxCurvedCharAngleOut="-25" maxCurvedCharAngleIn="25" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" geometryGeneratorType="PointGeometry" dist="0" placementFlags="10" placement="1" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" overrunDistanceUnit="MM" fitInPolygonOnly="0" layerType="PolygonGeometry" repeatDistance="0" overrunDistance="0" centroidInside="0" priority="5"/>
      <rendering obstacle="1" fontMaxPixelSize="10000" minFeatureSize="0" upsidedownLabels="0" labelPerPart="0" drawLabels="1" scaleMin="0" fontMinPixelSize="3" scaleMax="0" zIndex="0" displayAll="0" scaleVisibility="0" mergeLines="0" obstacleType="0" fontLimitPixelSize="0" maxNumLabels="2000" obstacleFactor="1" limitNumLabels="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties"/>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option value="pole_of_inaccessibility" name="anchorPoint" type="QString"/>
          <Option name="ddProperties" type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
          <Option value="false" name="drawToAllParts" type="bool"/>
          <Option value="0" name="enabled" type="QString"/>
          <Option value="&lt;symbol clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot; name=&quot;symbol&quot; type=&quot;line&quot; alpha=&quot;1&quot;>&lt;layer enabled=&quot;1&quot; class=&quot;SimpleLine&quot; pass=&quot;0&quot; locked=&quot;0&quot;>&lt;prop v=&quot;square&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;bevel&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;60,60,60,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;0.3&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; name=&quot;name&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; name=&quot;type&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol" type="QString"/>
          <Option value="0" name="minLength" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale" type="QString"/>
          <Option value="MM" name="minLengthUnit" type="QString"/>
          <Option value="0" name="offsetFromAnchor" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale" type="QString"/>
          <Option value="MM" name="offsetFromAnchorUnit" type="QString"/>
          <Option value="0" name="offsetFromLabel" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale" type="QString"/>
          <Option value="MM" name="offsetFromLabelUnit" type="QString"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
