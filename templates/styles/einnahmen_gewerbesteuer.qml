<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.10.1-A Coruña" labelsEnabled="1">
  <renderer-v2 forceraster="0" symbollevels="0" type="singleSymbol" enableorderby="0">
    <symbols>
      <symbol name="0" type="fill" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="35,139,69,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="76,76,76,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.2"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="coalesce(ramp_color(create_ramp(map(0,'#67000d',0.13,'#a50f15',0.26,'#cb181d',0.39,'#ef3b2c',0.52,'#fb6a4a',0.65,'#fc9272',0.78,'#fcbba1',0.9,'#fee0d2',1,'#fff5f0')),scale_linear(IF (&quot;gewerbesteuer&quot; > 0, NULL, &quot;gewerbesteuer&quot;), minimum(&quot;gewerbesteuer&quot;), 0, 0, 1)), '#238b45')" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
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
      <text-style fontStrikeout="0" fontSize="8" previewBkgrdColor="255,255,255,255" fontItalic="0" isExpression="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" textOpacity="1" fontLetterSpacing="0" multilineHeight="1" fontFamily="MS Shell Dlg 2" textOrientation="horizontal" fontKerning="1" fontCapitals="0" namedStyle="Standard" fontWordSpacing="0" fontUnderline="0" fontSizeUnit="Point" fieldName=" format_number(round( &quot;gewerbesteuer&quot;),0) || '€'" textColor="0,0,0,255" fontWeight="50" useSubstitutions="0" blendMode="0">
        <text-buffer bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSize="1" bufferJoinStyle="128" bufferNoFill="1" bufferOpacity="1" bufferDraw="1" bufferBlendMode="0" bufferColor="255,255,255,255" bufferSizeUnits="MM"/>
        <background shapeOffsetX="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeRotationType="0" shapeRadiiY="0" shapeSVGFile="" shapeJoinStyle="64" shapeBorderWidth="0" shapeBorderWidthUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeOffsetUnit="MM" shapeDraw="0" shapeRadiiX="0" shapeBorderColor="128,128,128,255" shapeSizeX="0" shapeOffsetY="0" shapeSizeType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiUnit="MM" shapeFillColor="255,255,255,255" shapeSizeY="0" shapeBlendMode="0" shapeType="0" shapeSizeUnit="MM" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0">
          <symbol name="markerSymbol" type="marker" force_rhr="0" alpha="1" clip_to_extent="1">
            <layer class="SimpleMarker" locked="0" enabled="1" pass="0">
              <prop k="angle" v="0"/>
              <prop k="color" v="243,166,178,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" value="" type="QString"/>
                  <Option name="properties"/>
                  <Option name="type" value="collection" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowDraw="0" shadowOffsetGlobal="1" shadowOffsetDist="1" shadowRadiusAlphaOnly="0" shadowScale="100" shadowBlendMode="6" shadowOpacity="0,7" shadowRadius="1,5" shadowColor="0,0,0,255" shadowOffsetUnit="MM" shadowOffsetAngle="135" shadowUnder="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusUnit="MM"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format reverseDirectionSymbol="0" plussign="0" useMaxLineLengthForAutoWrap="1" multilineAlign="0" wrapChar="" autoWrapLength="0" formatNumbers="0" addDirectionSymbol="0" decimals="3" placeDirectionSymbol="0" rightDirectionSymbol=">" leftDirectionSymbol="&lt;"/>
      <placement layerType="PolygonGeometry" offsetType="0" quadOffset="4" offsetUnits="MM" centroidWhole="0" distUnits="MM" repeatDistanceUnits="MM" xOffset="0" preserveRotation="1" distMapUnitScale="3x:0,0,0,0,0,0" dist="0" fitInPolygonOnly="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" placement="1" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="25" priority="5" repeatDistance="0" maxCurvedCharAngleOut="-25" geometryGeneratorType="PointGeometry" yOffset="0" centroidInside="0" geometryGenerator="" placementFlags="10" overrunDistance="0" geometryGeneratorEnabled="0" rotationAngle="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" overrunDistanceUnit="MM" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering obstacleFactor="1" maxNumLabels="2000" fontMinPixelSize="3" scaleMax="0" displayAll="0" limitNumLabels="0" fontLimitPixelSize="0" minFeatureSize="0" scaleMin="0" mergeLines="0" drawLabels="1" scaleVisibility="0" zIndex="0" upsidedownLabels="0" fontMaxPixelSize="10000" labelPerPart="0" obstacleType="0" obstacle="1"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" value="" type="QString"/>
          <Option name="properties"/>
          <Option name="type" value="collection" type="QString"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" value="pole_of_inaccessibility" type="QString"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
          <Option name="drawToAllParts" value="false" type="bool"/>
          <Option name="enabled" value="0" type="QString"/>
          <Option name="lineSymbol" value="&lt;symbol name=&quot;symbol&quot; type=&quot;line&quot; force_rhr=&quot;0&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; locked=&quot;0&quot; enabled=&quot;1&quot; pass=&quot;0&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; value=&quot;&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; value=&quot;collection&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString"/>
          <Option name="minLength" value="0" type="double"/>
          <Option name="minLengthMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="minLengthUnit" value="MM" type="QString"/>
          <Option name="offsetFromAnchor" value="0" type="double"/>
          <Option name="offsetFromAnchorMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="offsetFromAnchorUnit" value="MM" type="QString"/>
          <Option name="offsetFromLabel" value="0" type="double"/>
          <Option name="offsetFromLabelMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="offsetFromLabelUnit" value="MM" type="QString"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
